@Grapes([
    @Grab(group='org.elasticsearch.client', module='elasticsearch-rest-client', version='7.3.1'),
    @Grab(group='org.elasticsearch.client', module='elasticsearch-rest-high-level-client', version='7.3.1'),
    @Grab(group='org.semanticweb.elk', module='elk-owlapi', version='0.4.2'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-api', version='4.2.3'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-apibinding', version='4.2.3'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-impl', version='4.2.3'),
    @Grab(group='net.sourceforge.owlapi', module='owlapi-parsers', version='4.2.3'),
    @Grab(group='org.slf4j', module='slf4j-nop', version='1.7.25'),
    @Grab(group='ch.qos.reload4j', module='reload4j', version='1.2.18.5'),
    @GrabExclude(group='log4j', module='log4j'),
])


import groovy.json.*

import org.apache.http.auth.AuthScope
import org.apache.http.auth.UsernamePasswordCredentials
import org.apache.http.impl.client.BasicCredentialsProvider
import org.apache.http.impl.nio.client.HttpAsyncClientBuilder;
import org.apache.http.client.CredentialsProvider
import org.apache.http.HttpHost
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

import org.elasticsearch.client.indices.*
import org.elasticsearch.action.index.IndexRequest
import org.elasticsearch.common.xcontent.XContentType;
import org.elasticsearch.client.RestClientBuilder
import org.elasticsearch.client.RestClient
import org.elasticsearch.client.RequestOptions
import org.elasticsearch.client.RestHighLevelClient
import org.elasticsearch.index.reindex.DeleteByQueryRequest
import org.elasticsearch.index.query.MatchQueryBuilder
import org.elasticsearch.common.unit.TimeValue;

import java.nio.*
import java.nio.file.*
import java.util.*
import org.apache.logging.log4j.*
import java.net.URL

urls = args[0].split(",")
username = args[1]
password = args[2]
ontologyIndexName = args[3]
owlClassIndexName = args[4]
fileName = args[5]
skip_embbedding = args[6]

esUrls = new ArrayList<URL>();
hosts = new HttpHost[urls.length];
idx=0

for (String url:urls) {
	esUrl= new URL(url) 
	hosts[idx] = new HttpHost(esUrl.getHost(), esUrl.getPort(), esUrl.getProtocol());
	idx++;
}

restClient = null

if (!username.isEmpty() &&  !password.isEmpty()) {
	final CredentialsProvider credentialsProvider =
		new BasicCredentialsProvider();
	credentialsProvider.setCredentials(AuthScope.ANY,
		new UsernamePasswordCredentials(username, password));

	restClient = RestClient.builder(hosts)
		.setHttpClientConfigCallback(new RestClientBuilder.HttpClientConfigCallback() {
        @Override
        public HttpAsyncClientBuilder customizeHttpClient(
                HttpAsyncClientBuilder httpClientBuilder) {
            return httpClientBuilder
                .setDefaultCredentialsProvider(credentialsProvider);
        }
    });
} else {
	restClient = RestClient.builder(new HttpHost(esUrl.getHost(), esUrl.getPort(), esUrl.getProtocol()))
}

esClient = new RestHighLevelClient(restClient)

def indexExists(indexName) {
	try {
		GetIndexRequest request = new GetIndexRequest(indexName);
		return  esClient.indices().exists(request, RequestOptions.DEFAULT);
	}  catch (Exception e) {
		e.printStackTrace();
		return false;
	}
}

def initIndex() {
	def settings = [
	    "number_of_shards" : 1,
	    "number_of_replicas" : 1,
	    "analysis": [
			"normalizer": [
				"aberowl_normalizer": [
				"type": "custom",
				"filter": ["lowercase",]
				]
			]
	    ]
	]

    def ontologyIndexSettings = [
		"settings" : settings,
		"mappings":[
		"properties" : [
			"name": [
			"type": "keyword", "normalizer": "aberowl_normalizer"],
			"ontology": [
			"type": "keyword", "normalizer": "aberowl_normalizer"],
			"description": ["type": "text"],
		]
		]
    ]

	def classIndexSettings = [
		"settings" : settings,
		"mappings":[
		"properties" : [
			"embedding_vector": [
				"type": "binary",
				"doc_values": true
			],
			"class": ["type": "keyword"],
			"definition": ["type": "text"],
			"identifier": ["type": "keyword"],
			"label": [
			"type": "keyword", "normalizer": "aberowl_normalizer"],
			"ontology": [
			"type": "keyword", "normalizer": "aberowl_normalizer"],
			"oboid": [
			"type": "keyword", "normalizer": "aberowl_normalizer"],
			"owlClass": ["type": "keyword"],
			"synonyms": ["type": "text"],
		]
		]
	]

    if (!indexExists(ontologyIndexName)) {
		createIndex(ontologyIndexName, ontologyIndexSettings);
    }

	if (!indexExists(owlClassIndexName)) {
		createIndex(owlClassIndexName, classIndexSettings);
    }
}

def createIndex(indexName, settings) { 
	try {
		CreateIndexRequest request = new CreateIndexRequest(indexName);
		request.source(new JsonBuilder(settings).toString(), XContentType.JSON)
		CreateIndexResponse createIndexResponse = esClient.indices().create(request, RequestOptions.DEFAULT);
		println('Index created :' + indexName)
	}  catch (Exception e) {
		e.printStackTrace();
	}
}

def deleteOntologyData(ontology) {
	try {
		DeleteByQueryRequest request = new DeleteByQueryRequest(ontologyIndexName, owlClassIndexName);
		request.setQuery(new MatchQueryBuilder("ontology", ontology));
		request.setTimeout(new TimeValue(10 * 60000));
		response = esClient.deleteByQuery(request, RequestOptions.DEFAULT);
		println("total=" + response.total + "|deletedDocs=" + response.deleted + "|searchRetries=" 
			+ response.searchRetries + "|bulkRetries=" + response.bulkRetries)
	}  catch (Exception e) {
		e.printStackTrace();
	}
}

def index(def indexName, def obj) {
	try {
		request = new IndexRequest(indexName)
		request.source(new JsonBuilder(obj).toString(), XContentType.JSON);
		esClient.index(request, RequestOptions.DEFAULT);
    } catch (Exception e) {
		e.printStackTrace()
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
    
    index(ontologyIndexName, omap)

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
	    } else 
		if (aProp in identifiers) {
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
	// if (!deprecated) {

	info['deprecated'] = deprecated
	if (!hasLabel) {
	info["label"] << c.getIRI().getFragment().toString()
	}

	// Add an embedding to the document
	if (data["embeds"] != null && data["embeds"].containsKey(cIRI)) {
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
	
	
	index(owlClassIndexName, info)
	// }
    }

	println('Finished indexing :' + acronym)
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


if (skip_embbedding.equals("False")) {
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
}

indexOntology(fileName, data)  
esClient.close()
