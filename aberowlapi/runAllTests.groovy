/**
 * Test Runner for aberowl api.
 **/

@Grapes([
   @Grab(group='org.codehaus.groovy.modules.http-builder', module='http-builder', version='0.7' )
])

import groovy.util.GroovyTestSuite 
import junit.framework.Test 
import junit.textui.TestRunner

import test.src.AberowlManchesterOwlParserTest;
import test.src.SparqlApiTest;

class AllTests { 
   static Test suite() { 
      def allTests = new GroovyTestSuite() 
      allTests.addTestSuite(AberowlManchesterOwlParserTest.class) 
      allTests.addTestSuite(SparqlApiTest.class) 
      return allTests 
   } 
} 

TestRunner.run(AllTests.suite())