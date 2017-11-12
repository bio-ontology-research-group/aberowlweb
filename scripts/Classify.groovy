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
    incon = reasoner.getEquivalentClasses(fac.getOWLNothing()).getSize() - 1
    if (incon >= MAX_UNSATISFIABLE_CLASSES) {
	status = "Incoherent"
    } else {
	status = "Classified"
    }
    nb_classes = ont.getClassesInSignature().size();
    nb_individuals = ont.getIndividualsInSignature().size();
    nb_properties = ont.getObjectPropertiesInSignature().size();
    def q = [[fac.getOWLThing(), 0],] as Queue
    def used = new HashSet<OWLClass>();
    used.add(fac.getOWLThing());
    nb_visits = 0;
    nb_children = 0;
    max_children = 0;
    max_depth = 0;
    while(!q.isEmpty()) {
	def item = q.poll()
	def cur = item[0]
	def depth = item[1]
	def subs = reasoner.getSubClasses(cur, true).getFlattened();
	subs.remove(fac.getOWLNothing());
	def children = subs.size();
	nb_children += children;
	if (children > 0) nb_visits += 1;
	if (max_depth < depth) max_depth = depth;
	if (max_children < children) max_children = children;
	subs.each {cl ->
	    if (!used.contains(cl)) {
		used.add(cl);
		q.add([cl, depth + 1])
	    }
	}
    }

    avg_children = nb_children.intdiv(nb_visits);
    
} catch (Exception e) {
    status = "Unloadable"
    classifiable = false
    e.printStackTrace()
}

def json = JsonOutput.toJson([
	incon: incon, status: status, classifiable: classifiable,
	nb_classes: nb_classes, nb_individuals: nb_individuals,
	nb_properties: nb_properties, max_children: max_children,
	avg_children: avg_children, max_depth: max_depth])
println(json)
