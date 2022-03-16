@Grapes([
    @Grab(group='org.semanticweb.elk', module='elk-owlapi', version='0.4.2'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-api', version='4.2.3'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-apibinding', version='4.2.3'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-impl', version='4.2.3'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-parsers', version='4.2.3'),
    @Grab(group='org.slf4j', module='slf4j-nop', version='1.7.25'),
    @Grab(group='ch.qos.reload4j', module='reload4j', version='1.2.18.5'),
    @GrabExclude(group='log4j', module='log4j'),
])

import org.semanticweb.owlapi.model.parameters.*
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
import groovy.json.*

class URIShortFormProvider implements ShortFormProvider {

    public String getShortForm(OWLEntity entity) {
	return entity.toStringID();
    }

    public void dispose(){}
}

def MAX_UNSATISFIABLE_CLASSES = 500

def fileName = args[0]
def axiomsFileName = fileName + ".axms"
def incon = 0
def nb_classes = 0
def status = "Unknown"
def classifiable = true
try {
    OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
    OWLOntology ont = manager.loadOntologyFromOntologyDocument(new File(fileName));
    OWLOntologyImportsClosureSetProvider provider = new OWLOntologyImportsClosureSetProvider(manager, ont);
    OWLOntologyMerger merger = new OWLOntologyMerger(provider, false);
    ont = merger.createMergedOntology(manager, IRI.create("http://merged.owl"));

    OWLDataFactory fac = manager.getOWLDataFactory();
    ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor();
    OWLReasonerConfiguration config = new SimpleConfiguration(progressMonitor);
    ElkReasonerFactory f1 = new ElkReasonerFactory();
    OWLReasoner reasoner = f1.createReasoner(ont, config);
    reasoner.precomputeInferences();
    OWLObjectRenderer renderer = new ManchesterOWLSyntaxOWLObjectRendererImpl();
    renderer.setShortFormProvider(new URIShortFormProvider());
    InferredSubClassAxiomGenerator generator = new InferredSubClassAxiomGenerator();
    Set<OWLAxiom> axioms = generator.createAxioms(fac, reasoner);
    manager.addAxioms(ont, axioms);
    PrintWriter out = new PrintWriter(axiomsFileName);
    for (OWLAxiom axiom: ont.getTBoxAxioms(Imports.INCLUDED)) {
	String axm = renderer.render(axiom).replaceAll("[()]", "");
	out.println(axm);
    }
    out.close();
} catch (Exception e) {
    status = "Unloadable"
    classifiable = false
    e.printStackTrace()
}

def json = JsonOutput.toJson([classifiable: classifiable])
println(json)
