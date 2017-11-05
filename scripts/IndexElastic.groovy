@Grapes([
	@Grab(group='org.codehaus.groovy.modules.http-builder', module='http-builder', version='0.7.1' ),
	@Grab(group='org.semanticweb.elk', module='elk-owlapi', version='0.4.2'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-api', version='4.2.3'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-apibinding', version='4.2.3'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-impl', version='4.2.3'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-parsers', version='4.2.3'),
	@Grab(group='org.slf4j', module='slf4j-nop', version='1.7.25'),
	@Grab(group='org.apache.lucene', module='lucene-queryparser', version='7.1.0')
    ])

import groovy.json.*
import groovyx.net.http.HTTPBuilder
import groovyx.net.http.Method
import groovyx.net.http.ContentType

import org.apache.http.client.methods.*
import org.apache.http.entity.*
import org.apache.http.impl.client.*

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

import org.apache.lucene.queryparser.classic.QueryParser;


import java.nio.file.*

import org.apache.logging.log4j.*


def index(def type, def obj) {
    
    // delete if exists
    def m = ["query": ["bool": ["must": []]]]
    def ll = []
    ll << ["term" : ["ontology" : obj["ontology"]]]
    if (type == "owlClass") {
	ll << ["term" : ["class" : obj["class"]]]
    }
    ll.each {
	m.query.bool.must << it
    }
    try {
	http.post(
	    contentType: ContentType.JSON,
	    path: '/aberowl/' + type + '/_delete_by_query',
	    body: new JsonBuilder(m).toString()
	) {resp, reader -> }
    } catch (Exception e) {
	e.printStackTrace()
    }
    
    def j = new groovy.json.JsonBuilder(obj)
    try {

	http.handler.failure = { resp, reader ->
	    [response:resp, reader:reader]
	}
	http.handler.success = { resp, reader ->
	    [response:resp, reader:reader]
	}
	def response = http.post(
	    path: '/aberowl/'+ type + '/',
	    body: j.toPrettyString())
    } catch (Exception e) {
	e.printStackTrace()
	println "Failed: " + j.toPrettyString()
    }
}


void indexOntology(String fileName, def data) {

    OWLOntologyManager manager = OWLManager.createOWLOntologyManager()
    OWLOntology ont = manager.loadOntologyFromOntologyDocument(new File(fileName))
    OWLDataFactory fac = manager.getOWLDataFactory()
    ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor()
    OWLReasonerConfiguration config = new SimpleConfiguration(progressMonitor)
    ElkReasonerFactory f1 = new ElkReasonerFactory()
    OWLReasoner reasoner = f1.createReasoner(ont, config)
    def oReasoner = reasoner
    def df = fac
    
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


    def acronym = data.acronym
    def name = data.name
    def description = data.description
    def omap = [:]
    omap.query = [:]
    omap.query.term = [:]
    omap.query.term.ontology = acronym
    
    // Add record for the ontology itself
    omap = [:]
    omap.ontology = acronym
    omap.lontology = acronym.toLowerCase()
    omap.type = "ontology"
    omap.name = name
    omap.lname = name.toLowerCase()
    if (description) {
	omap.ldescription = StringEscapeUtils.escapeJava(description.toLowerCase())
	omap.description = StringEscapeUtils.escapeJava(description)
    }
    index("ontology", omap)

    // Re-add all classes for this ont

    OWLOntologyImportsClosureSetProvider mp = new OWLOntologyImportsClosureSetProvider(manager, ont)
    OWLOntologyMerger merger = new OWLOntologyMerger(mp, false)
    def iOnt = merger.createMergedOntology(manager, IRI.create("http://test.owl"))

    iOnt.getClassesInSignature(true).each {
	c -> // OWLClass
	def cIRI = c.getIRI().toString()
	def info = [
	    "owlClass": c.toString(),
	    "class": cIRI,
	    "ontology": acronym,
	].withDefault { key -> [] };

	def hasLabel = false
	def deprecated = false;

	EntitySearcher.getAnnotations(c, iOnt).each { annot ->
	    def aProp = annot.getProperty()
	    if (annot.isDeprecatedIRIAnnotation()) {
		deprecated = true
	    } else if (aProp in identifiers) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info["identifier"] << aVal
		}
	    } else if (aProp in labels) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info["label"] << aVal
		    hasLabel = true
		}
	    } else if (aProp in definitions) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info["definition"] << StringEscapeUtils.escapeJava(aVal)
		}
	    } else if (aProp in synonyms) {
		if (annot.getValue() instanceof OWLLiteral) {
		    def aVal = annot.getValue().getLiteral()
		    info["synonyms"] << aVal
		}
	    } 
	}

	if (!hasLabel) {
	    info["label"] << c.getIRI().getFragment().toString()
	}

	// generate OBO-style ID for the index
	def oboId = ""
	if (cIRI.lastIndexOf('?') > -1) {
	    oboId = cIRI.substring(cIRI.lastIndexOf('?') + 1)
	} else if (cIRI.lastIndexOf("#") > -1) {
	    oboId = cIRI.substring(cIRI.lastIndexOf("#") + 1)
	} else if (cIRI.lastIndexOf("/") > -1) {
	    oboId = cIRI.substring(cIRI.lastIndexOf("/") + 1)
	}
	if (oboId.length() > 0) {
	    oboId = oboId.replaceAll("_", ":").toLowerCase()
	    info["oboid"] = oboId
	}

	if (!deprecated) {
	    index("owlclass", info)
	}
    }

}

def url = args[0]
def fileName = args[1]

def data = System.in.newReader().getText()
def slurper = new JsonSlurper()
data = slurper.parseText(data)

http = new HTTPBuilder(url)

indexOntology(fileName, data)  

http.shutdown()
