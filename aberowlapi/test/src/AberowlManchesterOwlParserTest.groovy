package test.src;

import src.AberowlManchesterOwlParser;
import groovy.util.GroovyTestCase;

/**
 * Unit tests for aberowl manchester owl query parser.
 **/
public class AberowlManchesterOwlParserTest extends GroovyTestCase {
    
    private AberowlManchesterOwlParser parser = new AberowlManchesterOwlParser();

    void testParseWhenValueFrame() {
      def sparql = "VALUES ?abt {  \n" +
                    "   OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "       part_of some 'someclass' \n" +
                    "   } \n" +
                    "}";  
      def result = parser.parse(sparql);
      assertToString("subclass", result.queryType.trim())
      assertToString("https://www.w3.org/TR/owl2-manchester-syntax/", result.sparqlServiceUrl.trim())
      assertToString("", result.ontologyIri.trim())
      assertToString("part_of some 'someclass'", result.query.trim())
    }

    void testParseWhenFilterFrame() {
      def sparql = "FILTER ( ?abt in ( \n" +
                    "   OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "       part_of some 'someclass' \n" +
                    "   } \n" +
                    "))";    
      def result = parser.parse(sparql);
      assertToString("subclass", result.queryType.trim())
      assertToString("https://www.w3.org/TR/owl2-manchester-syntax/", result.sparqlServiceUrl.trim())
      assertToString("", result.ontologyIri.trim())
      assertToString("part_of some 'someclass'", result.query.trim())
    }

    void testParseSparqlWhenValueFrame() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       VALUES ?abt {  \n" +
                    "           OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "               part_of some 'someclass' \n" +
                    "           } \n" +
                    "       }. \n" +
                    "    }";  
      def result = parser.parseSparql(sparql);
      assertToString("subclass", result.queryType.trim())
      assertToString("https://www.w3.org/TR/owl2-manchester-syntax/", result.sparqlServiceUrl.trim())
      assertToString("", result.ontologyIri.trim())
      assertToString("part_of some 'someclass'", result.query.trim())
      assertTrue(result.isInValueFrame())
   }

   void testParseSparqlWhenFilterFrame() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "       FILTER ( ?abt in ( \n" +
                    "           OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "               part_of some 'someclass' \n" +
                    "           } \n" +
                    "       )) \n" +
                    "    }";    
      def result = parser.parseSparql(sparql);
      assertToString("subclass", result.queryType.trim())
      assertToString("https://www.w3.org/TR/owl2-manchester-syntax/", result.sparqlServiceUrl.trim())
      assertToString("", result.ontologyIri.trim())
      assertToString("part_of some 'someclass'", result.query.trim())
      assertFalse(result.isInValueFrame())
   }

   void testParseSparqlWhenNoAberowlManchesterOwlInQuery() {
       def sparql = " SELECT ?a ?b \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "    }"; 
      def result = parser.parseSparql(sparql);
      assertNull(result);
   }

    void testMatchManchesterOwlValueFrame() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       VALUES ?abt {  \n" +
                    "         OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "           part_of some 'someclass' \n" +
                    "         } \n" +
                    "       }. \n" +
                    "    }";  
      def result = parser.matchManchesterOwlValueFrame(sparql);
      def expected ="VALUES ?abt {  \n" +
                     "         OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                     "           part_of some 'someclass' \n" +
                     "         } \n" +
                     "       }.";
      assertToString(expected, result.trim())
   }

   void testMatchManchesterOwlValueFrameWhenNull() {
      try {
        def result = parser.matchManchesterOwlValueFrame(null);
        fail("Runtime exception not thrown")
      } catch (RuntimeException e) { }
   }

   void testMatchManchesterOwlValueFrameWhenEmpty() {
      def result = parser.matchManchesterOwlValueFrame("");
      assertToString("", result);
   }

   void testMatchManchesterOwlValueFrameWhenNoAberowlManchesterOwlInQuery() {
       def sparql = " SELECT ?a ?b \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "    }"; 
      def result = parser.matchManchesterOwlValueFrame(sparql);
      assertToString("", result);
   }

   void testMatchManchesterOwlFilterFrame() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "       FILTER ( ?abt in ( \n" +
                    "           OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "               part_of some 'someclass' \n" +
                    "           } \n" +
                    "       )) \n" +
                    "    }";  
      def result = parser.matchManchesterOwlFilterFrame(sparql);
      def expected ="FILTER ( ?abt in ( \n" +
                    "           OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "               part_of some 'someclass' \n" +
                    "           } \n" +
                    "       ))";
      assertToString(result.trim(), expected)
   }

   void testMatchManchesterOwlFilterWhenNull() {
      try {
        def result = parser.matchManchesterOwlFilterFrame(null);
        fail("Runtime exception not thrown")
      } catch (RuntimeException e) { }
   }

   void testMatchManchesterOwlFilterWhenEmpty() {
      def result = parser.matchManchesterOwlFilterFrame("");
      assertToString("", result);
   }

   void testMatchManchesterOwlFilterWhenNoAberowlManchesterOwlInQuery() {
       def sparql = " SELECT ?a ?b \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "    }"; 
      def result = parser.matchManchesterOwlFilterFrame(sparql);
      assertToString("", result);
   }

   void testRemoveAberowlManchesterOwlFrameWhenValueFrame() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "       VALUES ?abt {  \n" +
                    "         OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "            part_of some 'someclass' \n" + 
                    "         } \n" +
                    "       }. \n" +
                    "    }";  
      def result = parser.removeAberowlManchesterOwlFrame(sparql);
      def expected ="SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "        \n" + 
                    "    }"; 
      assertToString(expected, result.trim())
   }

   void testRemoveAberowlManchesterOwlFrameWhenValueFrameAndNotSelectVar() {
      def sparql = " SELECT ?a ?b \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       VALUES ?abt {  \n" +
                    "         OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "            part_of some 'someclass' \n" + 
                    "         } \n" +
                    "       }. \n" +
                    "    }";  
      def result = parser.removeAberowlManchesterOwlFrame(sparql);
      def expected ="SELECT ?a ?b \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "        \n" + 
                    "    }"; 
      assertToString(expected, result.trim())
   }

   void testRemoveAberowlManchesterOwlFrameWhenFilterFrame() {
      def sparql = " SELECT ?a ?b \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       FILTER ( ?abt in ( \n" +
                    "           OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "               part_of some 'someclass' \n" +
                    "           } \n" +
                    "       )) \n" +
                    "    }"; 
      def result = parser.removeAberowlManchesterOwlFrame(sparql);
      def expected ="SELECT ?a ?b \n" +
                  "   WHERE {\n" +
                  "       ?a rdf:label ?b .\n" +
                  "       }"; 
      assertToString(expected, result.trim())
   }

   void testReplaceAberowlManchesterOwlFrameWhenValueFrame() {
      def sparql = " SELECT ?a ?b \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       VALUES ?abt {  \n" +
                    "         OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "            part_of some 'someclass' \n" +
                    "         } \n" +
                    "       }. \n" +
                    "    }";  
      def commaJoinedClassesIriList = "<https://www.w3.org/TR/owl2-manchester-syntax/1>, <https://www.w3.org/TR/owl2-manchester-syntax/2>";
      def result = parser.replaceAberowlManchesterOwlFrame(sparql, commaJoinedClassesIriList);
      def expected ="SELECT ?a ?b \n" +
                     "   WHERE {\n" +
                     "       ?a rdf:label ?b .\n" +
                     "       VALUES ?abt {  \n" +
                     "         <https://www.w3.org/TR/owl2-manchester-syntax/1>, <https://www.w3.org/TR/owl2-manchester-syntax/2>}. \n" +
                     "    }";
      assertToString(expected, result.trim())
   }

   void testReplaceAberowlManchesterOwlFrameWhenValueFrameAndNoClassFound() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       VALUES ?abt {  \n" +
                    "         OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "            part_of some 'someclass' \n" +
                    "         } \n" +
                    "       }. \n" +
                    "    }";  
      def commaJoinedClassesIriList = "";
      def result = parser.replaceAberowlManchesterOwlFrame(sparql, commaJoinedClassesIriList);
      def expected ="SELECT ?a ?b ?abt \n" +
                     "   WHERE {\n" +
                     "       ?a rdf:label ?b .\n" +
                     "       VALUES ?abt {  \n" +
                     "         ''}. \n" +
                     "    }";
      assertToString(expected, result.trim())
   }

   void testReplaceAberowlManchesterOwlFrameWhenFilterFrame() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "       FILTER ( ?abt in ( \n" +
                    "           OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "               part_of some 'someclass' \n" +
                    "           } \n" +
                    "       )) \n" +
                    "    }"; 
      def commaJoinedClassesIriList = "<https://www.w3.org/TR/owl2-manchester-syntax/1>, <https://www.w3.org/TR/owl2-manchester-syntax/2>";
      def result = parser.replaceAberowlManchesterOwlFrame(sparql, commaJoinedClassesIriList);
      def expected ="SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "       FILTER ( ?abt in ( \n" +
                    "           <https://www.w3.org/TR/owl2-manchester-syntax/1>, <https://www.w3.org/TR/owl2-manchester-syntax/2>)) \n" +
                    "    }";
      assertToString(expected, result.trim())
   }

   void testReplaceAberowlManchesterOwlFrameWhenFilterFrameAndNoClassFound() {
      def sparql = " SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "       FILTER ( ?abt in ( \n" +
                    "           OWL subclass <https://www.w3.org/TR/owl2-manchester-syntax/> <> { \n" +
                    "               part_of some 'someclass' \n" +
                    "           } \n" +
                    "       )) \n" +
                    "    }"; 
      def commaJoinedClassesIriList = "";
      def result = parser.replaceAberowlManchesterOwlFrame(sparql, commaJoinedClassesIriList);
      def expected ="SELECT ?a ?b ?abt \n" +
                    "   WHERE {\n" +
                    "       ?a rdf:label ?b .\n" +
                    "       ?b rdf:type ?abt .\n" +
                    "       FILTER ( ?abt in ( \n" +
                    "           '')) \n" +
                    "    }";
      assertToString(expected, result.trim())
   }
}