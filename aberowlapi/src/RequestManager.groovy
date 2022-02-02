package src

// import org.semanticweb.elk.owlapi.ElkReasonerFactory;
// import org.semanticweb.elk.owlapi.ElkReasonerConfiguration
// import org.semanticweb.elk.reasoner.config.*
import org.semanticweb.HermiT.ReasonerFactory;
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
import com.google.common.collect.*
import org.semanticweb.owlapi.model.UnloadableImportException



public class RequestManager {
    private static final ELK_THREADS = "4"
    private static final MAX_UNSATISFIABLE_CLASSES = 500

    private static final MAX_REASONER_RESULTS = 100000

    OWLOntologyManager oManager;
    OWLDataFactory df = OWLManager.getOWLDataFactory();
    OWLReasoner oReasoner = null;
    OWLReasoner structReasoner = null;
    
    def ontology = null;
    def ont = null;
    def ontIRI = null;
    def queryEngine = null;

    def aProperties = [
    	df.getRDFSLabel(),
	df.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasNarrowSynonym")),
	df.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasBroadSynonym")),
	df.getOWLAnnotationProperty(IRI.create("http://www.geneontology.org/formats/oboInOwl#hasExactSynonym"))
    ];
    
    def identifiers = [
	df.getOWLAnnotationProperty(IRI.create('http://purl.org/dc/elements/1.1/identifier')),
    ];

    def labels = [
	df.getRDFSLabel(),
	df.getOWLAnnotationProperty(IRI.create('http://www.w3.org/2004/02/skos/core#prefLabel')),
	df.getOWLAnnotationProperty(IRI.create('http://purl.obolibrary.org/obo/IAO_0000111'))
    ];
    def synonyms = [
	df.getOWLAnnotationProperty(IRI.create('http://www.w3.org/2004/02/skos/core#altLabel')),
	df.getOWLAnnotationProperty(IRI.create('http://purl.obolibrary.org/obo/IAO_0000118')),
	df.getOWLAnnotationProperty(IRI.create('http://www.geneontology.org/formats/oboInOwl#hasExactSynonym')),
	df.getOWLAnnotationProperty(IRI.create('http://www.geneontology.org/formats/oboInOwl#hasSynonym')),
	df.getOWLAnnotationProperty(IRI.create('http://www.geneontology.org/formats/oboInOwl#hasNarrowSynonym')),
	df.getOWLAnnotationProperty(IRI.create('http://www.geneontology.org/formats/oboInOwl#hasBroadSynonym'))
    ];
    def definitions = [
	df.getOWLAnnotationProperty(IRI.create('http://purl.obolibrary.org/obo/IAO_0000115')),
	df.getOWLAnnotationProperty(IRI.create('http://www.w3.org/2004/02/skos/core#definition')),
	df.getOWLAnnotationProperty(IRI.create('http://purl.org/dc/elements/1.1/description')),
	df.getOWLAnnotationProperty(IRI.create('http://purl.org/dc/terms/description')),
	df.getOWLAnnotationProperty(IRI.create('http://www.geneontology.org/formats/oboInOwl#hasDefinition'))
    ];

    ShortFormProvider shortFormProvider;

    public RequestManager(String ont, String ontIRI) {
	this.ont = ont;
	this.ontIRI = ontIRI;
	this.shortFormProvider = new SimpleShortFormProvider();
    } 
    
    public static RequestManager create(String ont, String ontIRI) {
	RequestManager mgr = new RequestManager(ont, ontIRI);
	try {
	    println("Starting manager for $ont")
	    mgr.loadOntology()
	    mgr.createReasoner()
	    println("Finished loading $ont")
	    return mgr;
	} catch (UnloadableImportException e) {
	    println("Unloadable ontology $ont")
	    e.printStackTrace();
	    return null;
	} catch (Exception e) {
	    println("Failed loading $ont")
	    e.printStackTrace();
	    return null;
	}
    }

    /**
     * Load a new or replace an existing ontology
     *
     * @param name corresponding to name of the ontology in the database
     */
    void reloadOntology() {
	try {
	    println("Reloading the ontology $ont");
	    this.loadOntology();
	    this.createReasoner();
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

	def ontology = lManager.loadOntologyFromOntologyDocument(IRI.create(this.ontIRI));
	OWLOntologyImportsClosureSetProvider provider = new OWLOntologyImportsClosureSetProvider(lManager, ontology);
	OWLOntologyMerger merger = new OWLOntologyMerger(provider, false);
	ontology = merger.createMergedOntology(lManager, IRI.create("http://merged.owl"));

	this.ontology = ontology
	this.oManager = lManager
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

	OWLReasonerFactory reasonerFactory = new ReasonerFactory();
	OWLOntology ontology = this.ontology
	OWLOntologyManager manager = this.oManager
	// /* Configure Elk */
	// ReasonerConfiguration eConf = ReasonerConfiguration.getConfiguration()
	// eConf.setParameter(ReasonerConfiguration.NUM_OF_WORKING_THREADS, ELK_THREADS)
	// eConf.setParameter(ReasonerConfiguration.INCREMENTAL_MODE_ALLOWED, "true")

	// /* OWLAPI Reasoner config, no progress monitor */
	// OWLReasonerConfiguration rConf = new ElkReasonerConfiguration(
	//     ElkReasonerConfiguration.getDefaultOwlReasonerConfiguration(
	// 	new NullReasonerProgressMonitor()), eConf)
        ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor();
	OWLReasonerConfiguration rConf = new SimpleConfiguration(progressMonitor);
	this.oReasoner = reasonerFactory.createReasoner(ontology, rConf);
	this.oReasoner.precomputeInferences(InferenceType.values());

	StructuralReasonerFactory sReasonerFactory = new StructuralReasonerFactory()
	this.structReasoner = sReasonerFactory.createReasoner(ontology)
	
	def sForm = new NewShortFormProvider(
	    this.aProperties, preferredLanguageMap, manager);

	// dispose of old reasoners, close the threadpool
	queryEngine?.getoReasoner()?.dispose()

	// check if there are many many unsatisfiable classes, then switch to structural reasoner
	if (this.oReasoner.getEquivalentClasses(df.getOWLNothing()).getEntitiesMinusBottom().size() >= MAX_UNSATISFIABLE_CLASSES) {
	    this.oReasoner.dispose()
	    this.oReasoner = this.structReasoner;
	    queryEngine = new QueryEngine(this.oReasoner, sForm)
	    println "Successfully classified $ont but switched to structural reasoner"
	} else {
	    this.queryEngine = new QueryEngine(this.oReasoner, sForm)
	    println "Successfully classified $ont"
	}

	println "Classified $ont"
    }

    def toInfo(OWLEntity c, boolean axioms) {
	def o = this.ontology;
	def info = [
	    "owlClass": c.toString(),
	    "class": c.getIRI().toString(),
	    "ontology": this.ont,
	    "deprecated": false
	].withDefault {key -> []};

	def hasLabel = false;
	def hasAnnot = false;

	EntitySearcher.getAnnotationAssertionAxioms(c, o).each { axiom ->
	    hasAnnot = true;
	    def annot = axiom.getAnnotation();
	    def aProp = axiom.getProperty();
	    if (annot.isDeprecatedIRIAnnotation()) {
		info["deprecated"] = true
	    } else if (aProp in this.identifiers) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info['identifier'] << aVal
		}
	    } else if (aProp in this.labels) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info['label'] = aVal
		    hasLabel = true
		}
	    } else if (aProp in this.definitions) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info["definition"] << aVal
		}
	    } else if (aProp in this.synonyms) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info["synonyms"] << aVal
		}
	    } else {
		if (annot.getValue() instanceof OWLLiteral) {
		    try {
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
			    def prop = this.shortFormProvider.getShortForm(aProp)
			    info[prop].add(aVal)
			}
		    } catch (Exception e) {
		    }
		}
	    }
	}

	if (!hasLabel) {
	    info["label"] = this.shortFormProvider.getShortForm(c);
	}

	if (!hasAnnot) {
	    info["deprecated"] = true;
	}

	if (axioms) {
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
	}
	return info;
    }

    ArrayList<HashMap> classes2info(Set<OWLClass> classes, boolean axioms) {
	ArrayList<HashMap> result = new ArrayList<HashMap>();
	def o = this.ontology
	classes.each { c ->
	    def info = toInfo(c, axioms);
	    if (!info["deprecated"]) {
		result.add(info);
	    }
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
    Set runQuery(String mOwlQuery, String type, boolean direct, boolean labels, boolean axioms) {
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

	Set resultSet = Sets.newHashSet(Iterables.limit(queryEngine.getClasses(mOwlQuery, requestType, direct, labels), MAX_REASONER_RESULTS))
	resultSet.remove(df.getOWLNothing())
	resultSet.remove(df.getOWLThing())
	def classes = classes2info(resultSet, axioms);
	return classes.sort {x, y -> x["label"].compareTo(y["label"])};
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
    // Map getStats(String oString) {
    // 	def stats = []
    // 	OWLOntology ont = ontology
    // 	stats = [
    // 	    'axiomCount': 0,
    // 	    'classCount': ont.getClassesInSignature(true).size()
    // 	]
    // 	AxiomType.TBoxAxiomTypes.each { ont.getAxioms(it, true).each { stats.axiomCount += 1 } }
    // 	AxiomType.RBoxAxiomTypes.each { ont.getAxioms(it, true).each { stats.axiomCount += 1 } }

    // 	return stats
    // }
    
    
    /**
     * Retrieve all objects properties
     */
    def getObjectProperties() {
	return this.getObjectProperties(df.getOWLTopObjectProperty())
    }
    
    def getObjectProperties(String prop) {
	def objProp = df.getOWLObjectProperty(IRI.create(prop));
	return this.getObjectProperties(objProp);
    }
    
    def getObjectProperties(OWLObjectProperty prop) {

	def subProps = this.structReasoner.getSubObjectProperties(
	    prop, true).getFlattened()
	subProps.remove(df.getOWLBottomObjectProperty())
	subProps.remove(df.getOWLTopObjectProperty())
	def used = new HashSet<OWLObjectProperty>();
	def result = [];
	for (def expression: subProps) {
	    def objProp = expression.getNamedProperty()
	    if (!used.contains(objProp)) {
		result.add(toInfo(objProp, false));
		used.add(objProp);
	    }
	}
	return ["result": result.sort {x, y -> x["label"].compareTo(y["label"])}];
    }

    
}

