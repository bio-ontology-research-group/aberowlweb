package src

import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.elk.owlapi.ElkReasonerConfiguration
import org.semanticweb.elk.reasoner.config.*
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.reasoner.*
import org.semanticweb.owlapi.reasoner.structural.StructuralReasoner
import org.semanticweb.owlapi.vocab.OWLRDFVocabulary;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.io.*;
import org.semanticweb.owlapi.owllink.*;
import org.semanticweb.owlapi.util.*;
import org.semanticweb.owlapi.search.*;
import org.semanticweb.owlapi.manchestersyntax.renderer.*;
import org.semanticweb.owlapi.reasoner.structural.*

import java.util.concurrent.*
import java.util.concurrent.atomic.*
import java.util.timer.*

import groovy.json.*
import groovy.io.*
import groovyx.net.http.HTTPBuilder
import groovyx.net.http.Method
import groovyx.net.http.ContentType
import com.google.common.collect.*



class RequestManager {
    private static final ELK_THREADS = "64"
    private static final MAX_UNSATISFIABLE_CLASSES = 500

    private static final MAX_REASONER_RESULTS = 100000

    OWLOntologyManager oManager
    List<OWLAnnotationProperty> aProperties = new ArrayList<>();
    OWLDataFactory df = OWLManager.getOWLDataFactory();


    def ontology = null
    def ont = null
    def ontIRI = null
    def queryEngine = null
    def used = null
    
    RequestManager(String ont, String ontIRI) {
	this.ont = ont
	this.ontIRI = ontIRI
	try {
	    loadOntology()
	    loadAnnotations()
	    createReasoner()
	    println("Finished loading $ont")
	} catch (Exception e) {
	    println("Failed loading $ont")
	    e.printStackTrace();
	    System.exit(-1);
	}
    }

    /**
     * Load a new or replace an existing ontology
     *
     * @param name corresponding to name of the ontology in the database
     */
    void reloadOntology() {
	try {
	    OWLOntologyManager lManager = OWLManager.createOWLOntologyManager()
	    OWLOntologyLoaderConfiguration config = new OWLOntologyLoaderConfiguration()
	    config.setFollowRedirects(true)
	    config = config.setMissingImportHandlingStrategy(
		MissingImportHandlingStrategy.SILENT)
	    def ontology = lManager.loadOntologyFromOntologyDocument(IRI.create(this.ontIRI))
	    println "Updated ontology: " + this.ont
	    
	    this.ontology = ontology
	    this.ontologyManager = lManager

	    reloadOntologyAnnotations(this.ont)

	    List<String> langs = new ArrayList<>();
	    Map<OWLAnnotationProperty, List<String>> preferredLanguageMap = new HashMap<>();
	    for (OWLAnnotationProperty annotationProperty : this.aProperties) {
		preferredLanguageMap.put(annotationProperty, langs);
	    }
	    // May be replaced with any reasoner using the standard interface
	    OWLReasonerFactory reasonerFactory = new ElkReasonerFactory()
	    createOntologyReasoner(reasonerFactory, preferredLanguageMap)
	} catch (OWLOntologyInputSourceException e) {
	    e.printStackTrace()
	} catch (IOException e) {
	    e.printStackTrace()
	} catch (Exception e) {
	    e.printStackTrace()
	}
    }

    /**
     * Create the ontology manager and load it with the given ontology.
     * Create the ontology manager and load it with the given ontology.
     *
     * @throws OWLOntologyCreationException , IOException
     * @throws OWLOntologyCreationException , IOException
     */
    void loadOntology() throws OWLOntologyCreationException, IOException {
	OWLOntologyManager lManager = OWLManager.createOWLOntologyManager()
	OWLOntologyLoaderConfiguration config = new OWLOntologyLoaderConfiguration()
	config.setFollowRedirects(true)
	config = config.setMissingImportHandlingStrategy(MissingImportHandlingStrategy.SILENT)
	def ontology = lManager.loadOntologyFromOntologyDocument(IRI.create(this.ontIRI));
	this.ontology = ontology
	this.oManager = lManager
    }

    void createOntologyReasoner(OWLReasonerFactory reasonerFactory, Map preferredLanguageMap) throws Exception {
	OWLOntology ontology = this.ontology
	OWLOntologyManager manager = this.oManager
	/* Configure Elk */
	ReasonerConfiguration eConf = ReasonerConfiguration.getConfiguration()
	eConf.setParameter(ReasonerConfiguration.NUM_OF_WORKING_THREADS, this.ELK_THREADS)
	eConf.setParameter(ReasonerConfiguration.INCREMENTAL_MODE_ALLOWED, "true")

	/* OWLAPI Reasoner config, no progress monitor */
	OWLReasonerConfiguration rConf = new ElkReasonerConfiguration(ElkReasonerConfiguration.getDefaultOwlReasonerConfiguration(new NullReasonerProgressMonitor()), eConf)
	OWLReasoner oReasoner = reasonerFactory.createReasoner(ontology, rConf);
	oReasoner.precomputeInferences(InferenceType.CLASS_HIERARCHY);

	def sForm = new NewShortFormProvider(aProperties, preferredLanguageMap, manager);

	// dispose of old reasoners, close the threadpool
	queryEngine?.getoReasoner()?.dispose()

	// check if there are many many unsatisfiable classes, then switch to structural reasoner
	if (oReasoner.getEquivalentClasses(df.getOWLNothing()).getEntitiesMinusBottom().size() >= MAX_UNSATISFIABLE_CLASSES) {
	    oReasoner.dispose()
	    StructuralReasonerFactory sReasonerFactory = new StructuralReasonerFactory()
	    oReasoner = sReasonerFactory.createReasoner(ontology)
	    queryEngine = new QueryEngine(oReasoner, sForm)
	    println "Successfully classified $ont but switched to structural reasoner"
	} else {
	    this.queryEngine = new QueryEngine(oReasoner, sForm)
	    println "Successfully classified $ont"
	}
    }

    /**
     * Create and run the reasoning on the loaded OWL ontologies, creating a QueryEngine for each.
     */
    void createReasoner() {
	println "Classifying $ont"
	List<String> langs = new ArrayList<>();
	Map<OWLAnnotationProperty, List<String>> preferredLanguageMap = new HashMap<>();
	for (OWLAnnotationProperty annotationProperty : this.aProperties) {
	    preferredLanguageMap.put(annotationProperty, langs);
	}

	OWLReasonerFactory reasonerFactory = new ElkReasonerFactory();
	createOntologyReasoner(reasonerFactory, preferredLanguageMap)
	println "Classified $ont"
    }

    /**
     * Create list of RDFS_LABEL annotations to be used by the ShortFormProvider for a given ontology.
     */
    void reloadOntologyAnnotations() {
	OWLDataFactory factory = df
	OWLAnnotationProperty rdfsLabel = factory.getOWLAnnotationProperty(OWLRDFVocabulary.RDFS_LABEL.getIRI());
	aProperties.add(rdfsLabel)
	aProperties.add(factory.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasNarrowSynonym")))
	aProperties.add(factory.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasBroadSynonym")))
	aProperties.add(factory.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasExactSynonym")))
    }

    /**
     * Create list of RDFS_LABEL annotations to be used by the ShortFormProvider for all ontologies.
     */
    void loadAnnotations() {
	reloadOntologyAnnotations()
    }


    Set classes2info(Set<OWLClass> classes, String uri) {
	ArrayList result = new ArrayList<HashMap>();
	def o = this.ontology
	classes.each { c ->
	    def info = [
		"owlClass"  : c.toString(),
		"classURI"  : c.getIRI().toString(),
		"ontologyURI": uri.toString(),
		"remainder" : c.getIRI().getFragment(),
		"deprecated": false
	    ].withDefault {key -> []};

	    def identifiers = [
		df.getOWLAnnotationProperty(new IRI('http://purl.org/dc/elements/1.1/identifier')),
	    ]
	    
	    def labels = [
		df.getRDFSLabel(),
		df.getOWLAnnotationProperty(new IRI('http://www.w3.org/2004/02/skos/core#prefLabel')),
		df.getOWLAnnotationProperty(new IRI('http://purl.obolibrary.org/obo/IAO_0000111'))
	    ]
	    def synonyms = [
		df.getOWLAnnotationProperty(new IRI('http://www.w3.org/2004/02/skos/core#altLabel')),
		df.getOWLAnnotationProperty(new IRI('http://purl.obolibrary.org/obo/IAO_0000118')),
		df.getOWLAnnotationProperty(new IRI('http://www.geneontology.org/formats/oboInOwl#hasExactSynonym')),
		df.getOWLAnnotationProperty(new IRI('http://www.geneontology.org/formats/oboInOwl#hasSynonym')),
		df.getOWLAnnotationProperty(new IRI('http://www.geneontology.org/formats/oboInOwl#hasNarrowSynonym')),
		df.getOWLAnnotationProperty(new IRI('http://www.geneontology.org/formats/oboInOwl#hasBroadSynonym'))
	    ]
	    def definitions = [
		df.getOWLAnnotationProperty(new IRI('http://purl.obolibrary.org/obo/IAO_0000115')),
		df.getOWLAnnotationProperty(new IRI('http://www.w3.org/2004/02/skos/core#definition')),
		df.getOWLAnnotationProperty(new IRI('http://purl.org/dc/elements/1.1/description')),
		df.getOWLAnnotationProperty(new IRI('http://purl.org/dc/terms/description')),
		df.getOWLAnnotationProperty(new IRI('http://www.geneontology.org/formats/oboInOwl#hasDefinition'))
	    ]

	    def hasLabel = false

	    EntitySearcher.getAnnotations(c, o).each { annot ->
		if (annot.isDeprecatedIRIAnnotation()) {
		    info["deprecated"] = true
		}
		def aProp = annot.getProperty()
		if (aProp in identifiers) {
		    if (annot.getValue() instanceof OWLLiteral) {
			def aVal = annot.getValue().getLiteral()
			info['identifier'] << aVal
		    }
		} else if (aProp in labels) {
		    if (annot.getValue() instanceof OWLLiteral) {
			def aVal = annot.getValue().getLiteral()
			info['label'] << aVal
			hasLabel = true
		    }
		} else if (aProp in definitions) {
		    if (annot.getValue() instanceof OWLLiteral) {
			def aVal = annot.getValue().getLiteral()
			info["definition"] << aVal
		    }
		} else if (aProp in synonyms) {
		    if (annot.getValue() instanceof OWLLiteral) {
			def aVal = annot.getValue().getLiteral()
			info["synonyms"] << aVal
		    }
		} else {
		    if (annot.getValue() instanceof OWLLiteral) {
			def aVal = annot.getValue().getLiteral()
			def aLabels = EntitySearcher.getAnnotations(
			    aProp, o)
			if (aLabels.size() > 0) {
			    aLabels.each { l ->
				if (l.getValue() instanceof OWLLiteral) {
				    def lab = l.getValue().getLiteral()
				    info[lab].add(aVal)
				}
			    }
			} else {
			    def prop = aProp.toString()?.replaceAll("<", "")?.replaceAll(">", "")
			    info[prop].add(aVal)
			}
		    }
		}
	    }

	    if (!hasLabel) {
		info["label"] << c.getIRI().getFragment().toString()
	    }
	    info["first_label"] = info["label"][0]

	    // set up the renderer for the axioms
	    def sProvider = new AnnotationValueShortFormProvider(
		Collections.singletonList(df.getRDFSLabel()),
		Collections.<OWLAnnotationProperty, List<String>> emptyMap(),
		this.oManager);
	    def manSyntaxRenderer = new AberOWLSyntaxRendererImpl()
	    manSyntaxRenderer.setShortFormProvider(sProvider)

	    /* get the axioms */
	    EntitySearcher.getSuperClasses(c, o).each {
		cExpr -> // OWL Class Expression
		info["SubClassOf"] << manSyntaxRenderer.render(cExpr)
	    }
	    EntitySearcher.getEquivalentClasses(c, o).each {
		cExpr -> // OWL Class Expression
		info["Equivalent"] << manSyntaxRenderer.render(cExpr)
	    }
	    EntitySearcher.getDisjointClasses(c, o).each {
		cExpr -> // OWL Class Expression
	   	info["Disjoint"] << manSyntaxRenderer.render(cExpr)
	    }


	    result.add(info);
	}
	return result
    }

    /**
     * Iterate the query engines, collecting results from each and collating them into a single structure.
     *
     * @param mOwlQuery Class query in Manchester OWL Syntax.
     * @param requestType Type of class match to be performed. Valid values are: subclass, superclass, equivalent or all.
     * @return Set of OWL Classes.
     */
    Set runQuery(String mOwlQuery, String type, boolean direct, boolean labels) {
	def start = System.currentTimeMillis()

	type = type.toLowerCase()
	def requestType
	switch (type) {
	    case "superclass": requestType = RequestType.SUPERCLASS; break;
	    case "subclass": requestType = RequestType.SUBCLASS; break;
	    case "equivalent": requestType = RequestType.EQUIVALENT; break;
	    case "supeq": requestType = RequestType.SUPEQ; break;
	    case "subeq": requestType = RequestType.SUBEQ; break;
	    case "realize": requestType = RequestType.REALIZE; break;
	    default: requestType = RequestType.SUBEQ; break;
	}

	Set classes = new HashSet<>();
	Set resultSet = Sets.newHashSet(Iterables.limit(queryEngine.getClasses(mOwlQuery, requestType, direct, labels), MAX_REASONER_RESULTS))
	resultSet.remove(df.getOWLNothing())
	resultSet.remove(df.getOWLThing())
	classes.addAll(classes2info(resultSet, ont))

	def end = System.currentTimeMillis()

	return classes;
    }


    Set runQuery(String mOwlQuery, String type) {
	return runQuery(mOwlQuery, type, false)
    }

    /** This returns the direct R-successors of a class C in O
     class and relations are given as String-IRIs
     */
    Set relationQuery(String relation, String cl) {
	Set classes = new HashSet<>();

	def vOntUri = ont

	// get the direct subclasses of cl
	Set<OWLClass> subclasses = queryEngine.getClasses(cl, RequestType.SUBCLASS, true, false)
	// These are all the classes for which the R some C property holds
	String query1 = "<$relation> SOME $cl"
	Set<OWLClass> mainResult = queryEngine.getClasses(query1, RequestType.SUBCLASS, true, false)
	// Now remove all classes that are not specific to cl (i.e., there is a more specific class in which the R-edge can be created)
	subclasses.each { sc ->
	    String query2 = "$relation SOME " + sc.toString()
	    def subResult = queryEngine.getClasses(query2, RequestType.SUBCLASS, true, false)
	    mainResult = mainResult - subResult
	}
	classes.addAll(classes2info(mainResult, ont))
	return classes
    }

    Map<String, QueryEngine> getQueryEngine() {
	return this.queryEngine
    }

    /**
     * @return the oManager
     */
    OWLOntologyManager getoManager() {
	return oManager
    }

    /**
     * @return the ontologies
     */
    def getOntology() {
	return ontology
    }

    /**
     * Get the axiom count of all the ontologies
     */
    Map getStats(String oString) {
	def stats = []
	OWLOntology ont = ontology
	stats = [
	    'axiomCount': 0,
	    'classCount': ont.getClassesInSignature(true).size()
	]
	AxiomType.TBoxAxiomTypes.each { ont.getAxioms(it, true).each { stats.axiomCount += 1 } }
	AxiomType.RBoxAxiomTypes.each { ont.getAxioms(it, true).each { stats.axiomCount += 1 } }

	return stats
    }
    
    HashMap getInfoObjectProperty(String uriObjectProperty) {
	HashMap objectProperties = new HashMap<String, String>()
	OWLObjectProperty objectProperty = df.getOWLObjectProperty(IRI.create(uriObjectProperty));
	Iterator<OWLAnnotationAssertionAxiom> jt = EntitySearcher.getAnnotationAssertionAxioms(objectProperty, ontology).iterator();
	OWLAnnotationAssertionAxiom axiom;
	while (jt.hasNext()) {
	    axiom = jt.next();
	    if (axiom.getProperty().isLabel()) {
		OWLLiteral value = (OWLLiteral) axiom.getValue();
		objectProperties.put('classURI', axiom.getSubject().toString());
		objectProperties.put('label', value.getLiteral().toString());
	    }
	}
	return objectProperties;
    }


    /**
     * Retrieve all objects properties
     */
    Map getObjectProperties() {
	def reasoner = new StructuralReasoner(
	    this.ontology, new SimpleConfiguration(),
	    BufferingMode.NON_BUFFERING)
	this.used = new HashSet<OWLObjectProperty>()
	
	return this.getObjectProperties(reasoner, df.getOWLTopObjectProperty())
    }
    
    Map getObjectProperties(OWLReasoner reasoner, OWLObjectProperty prop) {
	def propMap = [:]
	def iter = EntitySearcher.getAnnotationAssertionAxioms(
	    prop, this.ontology).iterator()
	while (iter.hasNext()) {
	    def axiom = iter.next()
	    if (axiom.getProperty().isLabel()) {
		OWLLiteral value = (OWLLiteral) axiom.getValue()
		propMap["owlClass"] = "<" + axiom.getSubject().toString() + ">"
		propMap["label"] = value.getLiteral().toString()
		break
	    }
	}

	def subProps = reasoner.getSubObjectProperties(
	    prop, true).getFlattened()
	if (subProps.size() > 1) {
	    propMap["children"] = []
	    for (def expression: subProps) {
		def objProp = expression.getNamedProperty()
		if (this.used.contains(objProp)) {
		    continue
		} else {
		    this.used.add(objProp)
		}
		if (objProp != df.getOWLBottomObjectProperty()) {
		    def children = getObjectProperties(
			reasoner, objProp)
		    if(!children.isEmpty()) {
			propMap["children"].add(children)
		    }
		}
	    }
	}
	
	return propMap
    }

    
}

