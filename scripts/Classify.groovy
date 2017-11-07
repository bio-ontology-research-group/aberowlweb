@Grapes([
	  @Grab(group='org.semanticweb.elk', module='elk-owlapi', version='0.4.2'),
          @Grab(group='net.sourceforge.owlapi', module='owlapi-api', version='4.2.3'),
          @Grab(group='net.sourceforge.owlapi', module='owlapi-apibinding', version='4.2.3'),
	  @Grab(group='net.sourceforge.owlapi', module='owlapi-impl', version='4.2.3'),
          @Grab(group='net.sourceforge.owlapi', module='owlapi-parsers', version='4.2.3'),
	  @Grab(group='org.slf4j', module='slf4j-nop', version='1.7.25'),
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

def MAX_UNSATISFIABLE_CLASSES = 500

def fileName = args[0]
def incon = 0
def status = "Unknown"
def classifiable = true
try {
    OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
    OWLOntologyLoaderConfiguration loadConfig = new OWLOntologyLoaderConfiguration();
    loadConfig.setFollowRedirects(true);
    loadConfig = loadConfig.setMissingImportHandlingStrategy(MissingImportHandlingStrategy.SILENT);
    def source = new FileDocumentSource(new File(fileName));
    OWLOntology ont = manager.loadOntologyFromOntologyDocument(source, loadConfig);
    OWLDataFactory fac = manager.getOWLDataFactory();
    ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor();
    OWLReasonerConfiguration config = new SimpleConfiguration(progressMonitor);
    ElkReasonerFactory f1 = new ElkReasonerFactory();
    OWLReasoner reasoner = f1.createReasoner(ont, config);
    incon = reasoner.getEquivalentClasses(fac.getOWLNothing()).getSize() - 1
    if (incon >= MAX_UNSATISFIABLE_CLASSES) {
	status = "Incoherent"
    } else {
	status = "Classified"
    }
} catch (Exception e) {
    status = "Unloadable"
    classifiable = false
    e.printStackTrace()
}

def json = JsonOutput.toJson(
    [incon: incon, status: status, classifiable: classifiable])
println(json)
