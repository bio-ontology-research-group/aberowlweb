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
import groovyx.net.http.HttpResponseException
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

import java.nio.*
import java.nio.file.*
import java.util.*
import org.apache.logging.log4j.*


url = args[0]
indexName = args[1]
fileName = args[2]

http = new HTTPBuilder(url)

def indexExists(indexName) {
    try {
	http.get(
	    path: '/' + indexName,
	)
    } catch (HttpResponseException e) {
	r = e.response
	return r.status != 404
    }
    return true
}

def initIndex() {
    def settings = [
	"settings" : [
	    "number_of_shards" : 5,
	    "number_of_replicas" : 1,
	    "analysis": [
		"normalizer": [
		    "my_normalizer": [
			"type": "custom",
			"filter": ["lowercase",]
		    ]
		]
	    ]
	],
	"mappings" : [
            "owlclass" : [
		"properties" : [
                    "embedding_vector": [
			"type": "binary",
			"doc_values": true
		    ],
		    "class": ["type": "keyword"],
		    "definition": ["type": "text"],
		    "identifier": ["type": "keyword"],
		    "label": [
			"type": "keyword", "normalizer": "my_normalizer"],
		    "ontology": [
			"type": "keyword", "normalizer": "my_normalizer"],
		    "oboid": [
			"type": "keyword", "normalizer": "my_normalizer"],
		    "owlClass": ["type": "keyword"],
		    "synonyms": ["type": "text"],
		]
            ],
	    "ontology": [
		"properties" : [
		    "name": [
			"type": "keyword", "normalizer": "my_normalizer"],
		    "ontology": [
			"type": "keyword", "normalizer": "my_normalizer"],
		    "description": ["type": "text"],
		]
	    ]
	]
    ]
    if (!indexExists(indexName)) {
	try {
	    http.request(Method.PUT, ContentType.JSON) { req ->
		uri.path = '/' + indexName
		body = new JsonBuilder(settings).toString()
		response.success = {resp, json ->
		    println(json)
		}
		response.failure = {resp, json ->
		    println(json)
		}
	    }
	} catch (HttpResponseException e) {
	    e.printStackTrace()
	}
    }
}

def deleteOntologyData(ontology) {
    def query = ["query": ["term": ["ontology": ontology]]]
    try {
	http.post(
	    contentType: ContentType.JSON,
	    path: '/' + indexName + '/ontology/_delete_by_query',
	    body: new JsonBuilder(query).toString()
	) {resp, reader -> }
	http.post(
	    contentType: ContentType.JSON,
	    path: '/' + indexName + '/owlclass/_delete_by_query',
	    body: new JsonBuilder(query).toString()
	) {resp, reader -> }
    } catch (Exception e) {
	e.printStackTrace()
    }

}

def index(def type, def obj) {
        
    def j = new groovy.json.JsonBuilder(obj)
    try {
	http.request(Method.POST, ContentType.JSON) {
	    uri.path = '/' + indexName + '/'+ type + '/'
	    body = j.toString()
	    headers.'Content-Type' = 'application/json'
	}
    } catch (Exception e) {
	e.printStackTrace()
	println "Failed: " + j.toPrettyString()
    }
}


void indexOntology(String fileName, def data) {
    // Initialize index
    initIndex()
    
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
    omap.ontology = acronym
    omap.name = name
    if (description) {
	omap.description = StringEscapeUtils.escapeJava(description)
    }
    
    // Delete ontology data
    deleteOntologyData(acronym)
    
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
	if (!deprecated) {
	
	    if (!hasLabel) {
		info["label"] << c.getIRI().getFragment().toString()
	    }

	    // Add an embedding to the document
	    if (data["embeds"].containsKey(cIRI)) {
		info["embedding_vector"] = data["embeds"][cIRI];
	    }
	    
	    // generate OBO-style ID for the index
	    def oboId = ""
	    if (cIRI.lastIndexOf('?') > -1) {
		oboId = cIRI.substring(cIRI.lastIndexOf('?') + 1)
	    } else if (cIRI.lastIndexOf('#') > -1) {
		oboId = cIRI.substring(cIRI.lastIndexOf('#') + 1)
	    } else if (cIRI.lastIndexOf('/') > -1) {
		oboId = cIRI.substring(cIRI.lastIndexOf('/') + 1)
	    }
	    if (oboId.length() > 0) {
		oboId = oboId.replaceAll("_", ":")
		info["oboid"] = oboId
	    }
	    
	    
	    index("owlclass", info)
	}
    }
}

String convertArrayToBase64(double[] array) {
    final int capacity = 8 * array.length;
    final ByteBuffer bb = ByteBuffer.allocate(capacity);
    for (int i = 0; i < array.length; i++) {
	bb.putDouble(array[i]);
    }
    bb.rewind();
    final ByteBuffer encodedBB = Base64.getEncoder().encode(bb);
    return new String(encodedBB.array());
}

def data = System.in.newReader().getText()
def slurper = new JsonSlurper()
data = slurper.parseText(data)


// Read embeddings
def embeds = [:]

new File(fileName + ".embs").splitEachLine(" ") { it ->
    double[] vector = new double[it.size() - 1]
    for (int i = 1; i < it.size(); ++i) {
	vector[i - 1] = Double.parseDouble(it[i]);
    }
    embeds[it[0]] = convertArrayToBase64(vector);
}


data["embeds"] = embeds

indexOntology(fileName, data)  

http.shutdown()
