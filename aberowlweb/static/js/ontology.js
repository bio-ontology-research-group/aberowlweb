class Ontology extends React.Component {

    constructor(props) {
	super(props);
	var classesMap = new Map();
	var classes = props.ontology.classes;
	for (var i = 0; i < classes.length; i++) {
	    classesMap.set(classes[i].owlClass, classes[i]); 
	}
	var propsMap = new Map();
	var properties = props.ontology.properties;
	for (var i = 0; i < properties.length; i++) {
	    propsMap.set(properties[i].owlClass, properties[i]); 
	}
	var currentTab = 'Overview';
	this.state = {
	    ontology: props.ontology,
	    classesMap: classesMap,
	    propsMap: propsMap,
	    tabs: [
		'Overview', 'Browse', 'DLQuery', /*'SimilarClasses'*/, 'SPARQL',
		// 'Visualise', 'PubMed', 'Data', 'SPARQL',
		'Download'],
	    currentTab: currentTab,
	    selectedClass: null,
	    selectedProp: null,
	    dlQuery: null,
	    dlResults: [],
	    simResults: [],
	    search: '',
	    searchResults: [],
		searchResultsShow: false,
		format: 'text/html'
	};
    }

    componentWillMount() {
	const params = this.props.match.params;
	var classesMap = this.state.classesMap;
	var selectedClass = null;
	var that = this;
	if (params.tab == 'Browse' && params.owlClass !== undefined) {
	    const owlClass = decodeURIComponent(params.owlClass);
	    if (classesMap.has(owlClass)) {
		selectedClass = classesMap.get(owlClass);
		this.setState({ selectedClass: selectedClass });
	    } else {
		//path param with iri require double encoding
		fetch('/api/ontology/'+ that.state.ontology.acronym 
			+ '/root/' + encodeURIComponent(owlClass))
		    .then(function(response){ return response.json(); })
		    .then(function(data){
			var state = that.findRoot(owlClass, data);
			state.currentTab = 'Browse';
			that.setState(state);
		    });
	    }
	} else if (params.tab == 'DLQuery' && params.owlClass !== undefined && params.query !== undefined) {
	    const owlClass = decodeURIComponent(params.owlClass);
	    const dlQuery = params.query;
	    var queries = [];
	    if (classesMap.has(owlClass)) {
		selectedClass = classesMap.get(owlClass);
		this.setState({ selectedClass: selectedClass });
	    } else {
		queries.push(
			//path param with iri require double encoding
		    fetch('/api/ontology/'+ that.state.ontology.acronym 
			+ '/root/' + encodeURIComponent(owlClass))
		    .then((response) => response.json())
		);
	    }
	    queries.push(
		fetch('/api/dlquery?direct=true&axioms=true&query=' + encodeURIComponent(owlClass)
		      + '&ontology=' + this.state.ontology.acronym + '&type=' + params.query)
		    .then((response) => response.json())
		
	    );
	    Promise.all(queries)
		.then(function(data) {
		    var dlResults = [];
		    var state = that.state;
		    if(queries.length == 2) {
			state = that.findRoot(owlClass, data[0]);
			dlResults = data[1].result;
		    } else {
			dlResults = data[0].result;
		    }
		    state.dlResults = dlResults;
		    state.currentTab = 'DLQuery';
		    state.dlQuery = dlQuery;
		    that.setState(state);
		});
	}else if (params.tab == 'SimilarClasses' && params.owlClass !== undefined) {
	    const owlClass = decodeURIComponent(params.owlClass);
	    var cls = owlClass.substring(1, owlClass.length - 1);
	    var queries = [];
	    if (classesMap.has(owlClass)) {
		selectedClass = classesMap.get(owlClass);
		this.setState({ selectedClass: selectedClass });
	    } else {
		queries.push(
			//path param with iri require double encoding
		    fetch('/api/ontology/'+ that.state.ontology.acronym 
			+ '/root/' + encodeURIComponent(owlClass))
		    .then((response) => response.json())
		);
	    }
	    queries.push(
		fetch('/api/mostsimilar?class=' + encodeURIComponent(cls)
		      + '&ontology=' + this.state.ontology.acronym)
		    .then((response) => response.json())
		
	    );
	    Promise.all(queries)
		.then(function(data) {
		    var simResults = [];
		    var state = that.state;
		    if(queries.length == 2) {
			state = that.findRoot(owlClass, data[0]);
			simResults = data[1].result;
		    } else {
			simResults = data[0].result;
		    }
		    state.simResults = simResults;
		    state.currentTab = 'SimilarClasses';
		    that.setState(state);
		});
	} else if (params.tab == 'Property' && params.owlClass !== undefined){
	    const owlClass = decodeURIComponent(params.owlClass);
	    const selectedProp = this.state.propsMap.get(owlClass);
	    this.setState({ selectedProp: selectedProp, currentTab: 'Property' });
	}
	
    }

    findRoot(owlClass, data) {
	var q = data.result.slice();
	var it = 0;
	var classesMap = this.state.classesMap;
	var ontology = this.state.ontology;
	ontology.classes = data.result;
	while(it < q.length) {
	    var cl = q[it];
	    if ('children' in cl) {
		cl.collapsed = true;
		q.push(...cl.children);
	    }
	    classesMap.set(cl.owlClass, cl);
	    it++;
	}
	var selectedClass = classesMap.get(owlClass);
	var state = {
	    classesMap: classesMap,
	    selectedClass: selectedClass,
	    ontology: ontology
	};
	return state;
    }

    renderTab(tab) {
	var activeClass = '';
	var currentTab = this.state.currentTab;
	if (tab === currentTab || (tab == 'Browse' && currentTab == 'Property')) {
	    activeClass = 'active';
	}
	var obj = this.state.selectedClass;
	if (tab == 'SimilarClasses' && obj != null) {
	    return (
		<li role="presentation" className={activeClass}>
		    <a href={'#/' + tab + '/' + encodeURIComponent(obj.owlClass)}>{tab}</a>
		</li>
	    );
	}
	return (
		<li role="presentation" className={activeClass}>
		<a href={'#/' + tab}>{tab}</a>
		</li>
	);
    }
    
    renderTabs() {
	const tabs = this.state.tabs;
	const content = tabs.map(
	    (tab) => this.renderTab(tab)
	); 
	return (
	    <ul class="nav nav-tabs">
		{content}
	    </ul>
	);
    }

    renderTopics(topics){
	if (topics != null) {
            const content = topics.map(
		(topic) =>
		    <span class="label label-default aberowl-topic">{topic}</span>
            );
            return (
	    <div>
		{content}
	    </div>
	    );
	}
	return (<div></div>);
    }

    renderList(list){
	if (list != null) {
	    const content = list.join(', ');
            return (
	    <div>
		{content}
	    </div>
	    );
	}
	return (<div></div>);
    }

    renderOverview() {
	const ontology = this.state.ontology;
	var submission = ontology.submission;
	const metadata = [
	    ['Description', submission.description],
	    ['Version', submission.version],
	    ['Release date', submission.date_released],
	    ['Homepage', submission.home_page],
	    ['Documentation', submission.documentation],
	    ['Publication', submission.publication],
	    ['Ontology language', submission.has_ontology_language],
	    ['Class Count', submission.nb_classes],
	    ['Inconsistent classes', submission.nb_inconsistent],
	    ['Max children', submission.max_children],
	    ['Average children', submission.avg_children],
	    ['Max depth', submission.max_depth]
	];
	const content = metadata.map(
	    (data) =>
		<tr><td>{data[0]}</td><td>{data[1]}</td></tr>
	);
	return (
	    <div>
		<h2>Ontology metadata</h2>
		<table class="table table-hover">
		<tbody>
		{content}
	        </tbody>
		</table>
	    </div>
	);
    }

    innerHTML(htmlString) {
	const html = {__html: htmlString};
	return (<span dangerouslySetInnerHTML={html}></span>);
    }

    renderPropertyView() {
	const obj = this.state.selectedProp;
	if (obj == null) {
	    return (<h2>Please select an object property!</h2>);
	}
	const ignoreFields = new Set([
	    'collapsed',
	    'children',
	    'deprecated',
	    'owlClass'
	]);

	var that = this;
	var allFields = Object.keys(obj)
	    .filter((item) => !ignoreFields.has(item));
	allFields = new Set(allFields);
	var fields = [
	    'identifier', 'label', 'definition', 'class', 'ontology'];
	var fieldSet = new Set(fields);
	fields = fields.filter((item) => allFields.has(item));
	for (let item of allFields) {
	    if(!fieldSet.has(item)) {
		fields.push(item);
	    }
	}
	const htmlFields = new Set(['SubClassOf', 'Equivalent', 'Disjoint']);
	
	const data = fields.map(function(item) {
	    if (htmlFields.has(item)) {
		return [item, that.innerHTML(obj[item].toString())];
	    }
	    var value = obj[item];
	    if(value && value.constructor === Array) {
		value = value.join(', ');
	    }
	    return [item, value];
	});
	const content = data.map(
	    (item) =>
		<tr><td>{ item[0] }</td><td>{ item[1] }</td></tr>
	);
	return (
	    <div>
		<table class="table table-hover">
		<thead>
		<th> Property </th> <th> Value </th>
	        </thead>
		<tbody>
		{content}
	        </tbody>
	        </table>
	    </div>
	);
    }

    renderBrowse() {
	const obj = this.state.selectedClass;
	if (obj == null) {
	    return (
		<div> Please select an ontology class. </div>
	    );
	}
	const ignoreFields = new Set([
	    'collapsed',
	    'children',
	    'deprecated',
	    'owlClass'
	]);

	var that = this;
	var allFields = Object.keys(obj)
	    .filter((item) => !ignoreFields.has(item));
	allFields = new Set(allFields);
	var fields = [
	    'identifier', 'label', 'definition', 'class', 'ontology',
	    'Equivalent', 'SubClassOf', 'Disjoint'];
	var fieldSet = new Set(fields);
	fields = fields.filter((item) => allFields.has(item));
	for (let item of allFields) {
	    if(!fieldSet.has(item)) {
		fields.push(item);
	    }
	}
	const htmlFields = new Set(['SubClassOf', 'Equivalent', 'Disjoint']);
	
	const data = fields.map(function(item) {
	    if (htmlFields.has(item)) {
		return [item, that.innerHTML(obj[item].toString())];
	    }
	    var value = obj[item];
	    if(value && value.constructor === Array) {
		value = value.join(', ');
	    }
	    return [item, value];
	});
	
	const content = data.map(
	    (item) =>
		<tr><td>{ item[0] }</td><td>{ item[1] }</td></tr>
	);
	return (
	    <div>
		<table class="table table-hover">
		<thead>
		<th> Annotation </th> <th> Value </th>
	        </thead>
		<tbody>
		{content}
	        </tbody>
		</table>
	    </div>
	);
    }

    renderDLQueryButtons(obj) {
	const buttons = [
	    ['subclass', 'Subclasses'],
	    ['subeq', 'Sub and Equivalent'],
	    ['equivalent', 'Equivalent'],
	    ['superclass', 'Superclasses'],
	    ['supeq', 'Super and Equivalent']
	];

	const dlQuery = this.state.dlQuery;
	
	const content = buttons.map(function(item) {
	    var activeClass = '';
	    if (dlQuery == item[0]) activeClass = 'active';
	    return (
		    <li role="presentation" className={ activeClass }>
		    <a href={'#/DLQuery/' + encodeURIComponent(obj) + '/' + item[0]}> { item[1] } </a>
		    </li>
	    );	    
	});

	return (
		<ul class="nav nav-pills">{ content }</ul>
	);
    }

    
	renderDLQuery() {
		var obj = this.state.dlQueryExp;
		const dlqueryInput = (
			<div layout="row">
				<form>
					<div class="form-group margin-top-15">
						<input class="form-control" type="text" id="dlquery" placeholder="Query" value={this.state.dlQueryExp} 
							onChange={(e) => this.onDlQueryChange(e)}/>
					</div>
				</form>
			</div>
		);

	
		const fields = [
			'OWLClass',
			'Label',
			'Definition',
		];
		
		const header = fields.map(
			(item) => <th>{ item }</th>);
		const dlResults = this.state.dlResults;
		
		const content =  dlResults.map(
			(item) =>
			<tr>
			<td><a href={'#/Browse/' + encodeURIComponent(item.owlClass)}>{ item.owlClass }</a></td> 
			<td>{ item.label }</td>
			<td>{ item.definition }</td>
			</tr>
		);
		return (
			<div>
			{ dlqueryInput }
			{ this.renderDLQueryButtons(obj) }
			<table class="table table-hover">
			<thead>{ header }</thead>
			<tbody>
			{ content }
				</tbody>
			</table>
			</div>
		);
	}
	
	onDlQueryChange(event) {
		this.setState({dlQueryExp: event.target.value, dlQuery:null});
	}

    renderSPARQL() {
		const formats = [
			{name: 'HTML',  format:'text/html'},
			{name: 'XML',  format:'application/sparql-results+xml'},
			{name: 'JSON',  format:'application/sparql-results+json'},
			{name: 'Javascript',  format:'application/javascript'},
			{name: 'Turtle',  format:'text/turtle'},
			{name: 'RDF/XML',  format:'application/rdf+xml'},
			{name: 'N-Triples',  format:'text/plain'},
			{name: 'CSV',  format:'text/csv'},
			{name: 'TSV',  format:'text/tab-separated-values'}
		];

		const formatOptions = formats.map((item) => <option value={ item.format }>{ item.name }</option> );

		const exampleContent = (
			<ul>
				<li>List of 'metabolite replacement' procedures and phenotypes corrected in DDIEM with aberowl Values form query. 
					<a href='#/SPARQL' onClick={(e) => this.setDDIEMExampleQuery(e)}> Show Query </a></li>
				<li>List of 'metabolite replacement' procedures and phenotypes corrected in DDIEM with aberowl Filter form query. 
					<a href='#/SPARQL' onClick={(e) => this.setDDIEMFilterExampleQuery(e)}> Show Query </a></li>
				<li>Retreive interacting proteins involved in 'response to hypoxia' from BioGateway Sparql endpoint. <a href='#/SPARQL' onClick={(e) => this.setBioGatewayExampleQuery(e)}> Show Query </a></li>
			</ul>
		);
		return (
			<div>
				<form onSubmit={(e) => this.executeSparql(e)}>
					<div layout="row">
						<div class="form-group margin-top-15">
							<textarea class="form-control" id="sparql" rows="10" col="5" placeholder="SPARQL Query" value={this.state.query}
							onChange={(e) => this.onSparqlChange(e)}></textarea>
						</div>
					</div>
					<div layout="row">
						<label for="format">Results Format</label>
						<select class="form-control" onChange={(e) => this.onFormatChange(e)} value={this.state.format}>
							{formatOptions}
						</select>
					</div>
					<div layout="row" class="margin-top-15">
						<button type="submit" class="btn btn-primary">Execute</button>
					</div>
				</form>
				{/* <div layout="row" class="margin-top-15 result-container"> {resultDisplay} </div> */}
				<div layout="row" class="margin-top-15"> 
				<h4>Example Queries</h4>
				{exampleContent} 
				</div>
			</div>
        );
	}

	onSparqlChange(event) {
		this.setState({query: event.target.value});
	}

	onFormatChange(event) {
		console.log(event)
		this.setState({format: event.target.value});
	}

	setDDIEMExampleQuery(event) {
		const query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>   \n" +
		"PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>   \n" +
		"PREFIX obo: <http://purl.obolibrary.org/obo/>   \n" +
		"SELECT ?procedure ?evidenceCode ?phenotypeCorrected   \n" +
		"FROM <http://ddiem.phenomebrowser.net>   \n" +
		"WHERE {   \n" +
		"	VALUES ?procedureType {     \n" +
		"		OWL equivalent <http://ddiem.phenomebrowser.net/sparql> <DDIEM> {     \n" +
		"			'metabolite replacement'    \n" +
		"		}     \n" +
		"	} .     \n" +
		"	?procedure rdf:type ?procedureType .   \n" +
		"	?procedure obo:RO_0002558 ?evidenceCode .   \n" +
		"	?procedure obo:RO_0002212 ?phenotypes .   \n" +
		"	?phenotypes rdfs:label ?phenotypeCorrected .   \n" +
		"}";
		this.setState({query: query});
	}

	setDDIEMFilterExampleQuery(event) {
		const query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>      \n" +
		"PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>   \n" +
		"PREFIX obo: <http://purl.obolibrary.org/obo/>   \n" +   
		"SELECT ?procedure ?evidenceCode ?phenotypeCorrected   \n" +   
		"FROM <http://ddiem.phenomebrowser.net>    \n" +  
		"WHERE {    \n" +     
		"	?procedure rdf:type ?procedureType .    \n" +  
		"	?procedure obo:RO_0002558 ?evidenceCode .     \n" + 
		"	?procedure obo:RO_0002212 ?phenotypes .      \n" +
		"	?phenotypes rdfs:label ?phenotypeCorrected .      \n" +
		"	FILTER ( ?procedureType in (    \n" +
		"		OWL equivalent <http://ddiem.phenomebrowser.net/sparql> <DDIEM> {     \n" +   
		"			'metabolite replacement'       \n" +
		"		}        \n" +
		"	) ).     \n" +
		"}";
		this.setState({query: query});
	}

	setBioGatewayExampleQuery(event) {
		const query = "SELECT ?interacting_protein ?gene   \n" +
		"WHERE   \n" +
		"{   \n" +
		"    ?interacting_protein <http://purl.obolibrary.org/obo/RO_0002331> ?gene .   \n" +
		"    VALUES ?gene {    \n" +
		"          OWL equivalent <https://biogw-db.nt.ntnu.no:4333/sparql> <GO> {    \n" +
		"             'response to hypoxia'   \n" +
		"          }    \n" +
		"    } .  \n" +  
		"}";
		this.setState({query: query});
	}
	

	executeSparql(event) {
		event.preventDefault();
		const query = this.state.query;	
		const format = this.state.format;	
		var that = this;
		const sparqlUrl = '/api/sparql?query=' + encodeURIComponent(query) + '&format=' + encodeURIComponent(format)
		window.open(sparqlUrl, "_blank") 
	}

    renderSimilarClasses() {
	const obj = this.state.selectedClass;
	if (obj == null) {
	    return (
		<h2> Please select an ontology class. </h2>
	    );
	}
	
	const fields = [
	    'OWLClass',
	    'Label',
	    'Definition',
	];
	
	const header = fields.map(
	    (item) => <th>{ item }</th>);
	const simResults = this.state.simResults;
	
	const content = simResults.map(
	    (item) =>
		<tr>
		<td><a href={'#/Browse/' + encodeURIComponent(item.owlClass)}>{ item.owlClass }</a></td>
		<td>{ item.label[0] }</td>
		<td>{ item.definition }</td>
		</tr>
	);
	return (
	    <div>
		<table class="table table-hover">
		<thead>{ header }</thead>
		<tbody>
		{ content }
	        </tbody>
		</table>
	    </div>
	);
    }

    renderDownload() {
	const downloads = this.state.ontology.downloads;
	const fields = [
	    'Version',
	    'Release date',
	    'Download',
	];
	const header = fields.map(
	    (item) => <th>{ item }</th>);
	const content = downloads.map(
	    (item) =>
		<tr>
		<td>{ item[0] }</td>
		<td>{ item[1] }</td>
		<td><a href={ '/' + item[2] }>Download</a></td>
		</tr>
	);
	return (
	    <div>
		<table class="table table-hover">
		<thead>{ header }</thead>
		<tbody>
		{ content }
	        </tbody>
		</table>
	    </div>
	);
    }

    renderCurrentTab() {
	const renders = {
	    'Overview': this.renderOverview(),
	    'Browse': this.renderBrowse(),
	    'DLQuery': this.renderDLQuery(),
	    // 'SimilarClasses': this.renderSimilarClasses(),
	    'SPARQL': this.renderSPARQL(),
	    'Download': this.renderDownload(),
	    'Property': this.renderPropertyView()
	};
	let currentTab = this.state.currentTab;
	if (currentTab in renders) return renders[currentTab];
	return (
	    <h2> Render not implemented yet! </h2>
	);
    }

    renderTreeNode(node) {
	var activeClass = '';
	const sClass = this.state.selectedClass;
	if (sClass != null && sClass.owlClass == node.owlClass) {
	    activeClass = 'active';
	}

	if ('children' in node && node.collapsed) {
	    return (
		<li class={activeClass}>
		    <span><i class="glyphicon glyphicon-minus" onClick={(e) => this.handleNodeClick(e, node.owlClass)}/></span>
		    <a href={'#/Browse/' + encodeURIComponent(node.owlClass)} onClick={(e) => this.handleNodeClick(e, node.owlClass)}> {node.label} </a>
		{this.renderTree(node.children)}
		</li>
	    );
	}
	var cClass = 'glyphicon-plus';
	if (node.collapsed) {
	    cClass = 'glyphicon-minus';
	}
	return (
	    <li class={activeClass}>
		<span><i className={'glyphicon ' + cClass} onClick={(e) => this.handleNodeClick(e, node.owlClass)}/></span>
		<a href={'#/Browse/' + encodeURIComponent(node.owlClass)} onClick={(e) => this.handleNodeClick(e, node.owlClass)}> {node.label} </a>
	    </li>
	);
    }
    
    renderTree(nodes) {
	const content = nodes.filter((node) => !node.deprecated).map(
	    (node) => this.renderTreeNode(node)
	);
	return (
		<ul>{content}</ul>
	);
    }

    componentWillReceiveProps(newProps) {
	const params = newProps.match.params;
	var currentTab = params.tab;
	var state = {
	    currentTab: currentTab
	};
	var that = this;
	if (currentTab == 'Browse' && params.owlClass !== undefined) {
	    var owlClass = decodeURIComponent(params.owlClass);
	    var classesMap = this.state.classesMap;
	    if (classesMap.has(owlClass)) {
		var obj = classesMap.get(owlClass);
		state.selectedClass = obj;
		state.dlQueryExp =  state.selectedClass ?  state.selectedClass.label.toLowerCase() : null;
		state.dlQueryExp =  state.dlQueryExp && state.dlQueryExp.includes(' ') ? "\'" + state.dlQueryExp +  "\'" : state.dlQueryExp;
		state.dlQuery=null;
		state.dlResults=[];
		if (!('children' in obj)) {
		    fetch(
			'/api/dlquery?direct=true&axioms=true&query='
			    + encodeURIComponent(obj.owlClass) + '&type=subclass&ontology=' + obj.ontology)
			.then(function(response){
			    return response.json();
			})
			.then(function(data) {
			    obj.children = data.result;
			    for (var i = 0; i < obj.children.length; i++) {
				classesMap.set(obj.children[i].owlClass, obj.children[i]);
			    }
			    state.classesMap = classesMap;
			    that.setState(state);
			});
		} else {
		    this.setState(state);
		}
	    } else {
		fetch('/api/ontology/'+ that.state.ontology.acronym 
		//path param with iri require double encoding
		+ '/root/' + encodeURIComponent(owlClass))
		    .then(function(response){ return response.json(); })
		    .then(function(data){
			var state = that.findRoot(owlClass, data);
			state.currentTab = 'Browse';
			that.setState(state);
		    });
	    }
	} else if (currentTab == 'DLQuery' && params.owlClass !== undefined && params.query !== undefined) {
	    const owlClass = decodeURIComponent(params.owlClass);
	    var queries = [];
	    const dlQuery = params.query;
	    fetch('/api/dlquery?axioms=true&labels=true&type=' + params.query
		  + '&query=' + encodeURIComponent(owlClass)
		  + '&ontology=' + this.state.ontology.acronym)
	    .then((response) => response.json())
	    .then(function(data) {
		var dlResults = [];
		state.dlResults = data.result;
		state.dlQuery = dlQuery
		that.setState(state);
	    });
	} else if (currentTab == 'SimilarClasses' && params.owlClass !== undefined) {
	    const owlClass = decodeURIComponent(params.owlClass);
	    const cls = owlClass.substring(1, owlClass.length - 1);
	    var queries = [];
	    fetch('/api/mostsimilar?class=' + encodeURIComponent(cls)
		  + '&ontology=' + this.state.ontology.acronym)
	    .then((response) => response.json())
	    .then(function(data) {
		var simResults = [];
		if (data.status == 'ok') {
		    state.simResults = data.result;
		    that.setState(state);
		} else {
		    state.simResults = [];
		    that.setState(state);
		}
	    });
	} else if (currentTab == 'Property' && params.owlClass !== undefined){
	    const owlClass = decodeURIComponent(params.owlClass);
	    var propsMap = this.state.propsMap;
	    const obj = propsMap.get(owlClass);
	    state.selectedProp = obj;
	    if (!('children' in obj)) {
		fetch(
		    '/api/ontology/' + obj.ontology + '/objectproperty/' + encodeURIComponent(obj.class))//path param with iri require double encoding
		    .then(function(response){
			return response.json();
		    })
		    .then(function(data) {
			obj.children = data.result;
			for (var i = 0; i < obj.children.length; i++) {
			    propsMap.set(obj.children[i].owlClass, obj.children[i]);
			}
			state.propsMap = propsMap;
			that.setState(state);
		    });
	    } else {
		this.setState(state);
	    }
	} else {
		this.setDDIEMExampleQuery();
	    this.setState(state);
	}
	
    }

    handleNodeClick(e, owlClass) {
	e.preventDefault();
	var classesMap = this.state.classesMap;
	var obj = classesMap.get(owlClass);
	this.props.history.push('/Browse/' + encodeURIComponent(owlClass));
	if (obj.collapsed) {
	    obj.collapsed = false;
	} else {
	    obj.collapsed = true;
	}
	this.setState({classesMap: classesMap});

    }


    renderProperty(node) {
	var activeClass = '';
	const sProp = this.state.selectedProp;
	if (sProp != null && sProp.owlClass == node.owlClass) {
	    activeClass = 'active';
	}

	if ('children' in node && node.collapsed) {
	    return (
		<li class={activeClass}>
		    <span><i class="glyphicon glyphicon-minus" onClick={(e) => this.handlePropertyClick(e, node.owlClass)}/></span>
		    <a href={'#/Property/' + encodeURIComponent(node.owlClass)} onClick={(e) => this.handlePropertyClick(e, node.owlClass)}> {node.label} </a>
		{this.renderObjectProperties(node.children)}
		</li>
	    );
	}
	var cClass = 'glyphicon-plus';
	if (node.collapsed) {
	    cClass = 'glyphicon-minus';
	}
	return (
	    <li class={activeClass}>
		<span><i className={'glyphicon ' + cClass} onClick={(e) => this.handlePropertyClick(e, node.owlClass)}/></span>
		<a href={'#/Property/' + encodeURIComponent(node.owlClass)} onClick={(e) => this.handlePropertyClick(e, node.owlClass)}> {node.label} </a>
	    </li>
	);
    }
    
    renderObjectProperties(properties) {
	const content = properties.map(
	    (node) => this.renderProperty(node)
	);
	return (
		<ul>{content}</ul>
	);
    }

    handlePropertyClick(e, owlClass) {
	e.preventDefault();
	var propsMap = this.state.propsMap;
	var obj = propsMap.get(owlClass);
	this.props.history.push('/Property/' + encodeURIComponent(owlClass));
	if ('collapsed' in obj && obj.collapsed) {
	    obj.collapsed = false;
	} else {
	    obj.collapsed = true;
	}
	this.setState({propsMap: propsMap});

    }

    handleSearchChange(e) {
	const value = e.target.value;
	this.setState({search: value});
	if (value.length >= 3) {
	    this.setState({searchResultsShow: true});
	    this.executeSearch(value);
	} else {
	    this.setState({searchResultsShow: false});
	}
    }

    executeSearch(search) {
	var that = this;
	fetch('/api/class/_startwith?query=' + encodeURIComponent(search)
		  + '&ontology=' + this.state.ontology.acronym)
	    .then((response) => response.json())
	    .then(function(data) {
		if (data.status == 'ok') {
		    that.setState({ searchResults: data.result });
		}
	    });
    }

    renderSearchForm() {
	return (
	    <form class="form">
		<div class="form-group">
		<input class="form-control" type="text"
	            value={this.state.search} onChange={(e) => this.handleSearchChange(e)}
		    placeholder="Search"/>
		</div>
	    </form>
	);
    }

    handleSearchItemClick(search) {
	this.setState({ search: search, searchResultsShow: false });
    }

    renderSearchResults() {
	var results = this.state.searchResults;
	const content = results.map(
	    (item) => 
		<li>
		<a href={'#/Browse/' + encodeURIComponent(item.owlClass)}
	            onClick={(e) => this.handleSearchItemClick(item.label[0])}>{item.label[0]}</a></li>
	);
	var open = '';
	if (this.state.searchResultsShow) {
	    open = 'open';
	}
	return (
		<div className={'dropdown ' + open}>
		<ul class="dropdown-menu">{content}</ul>
	    </div>
	);
    }
    
    render() {
	const ontology = this.state.ontology;
	return (
	    <div class="container">
		<div class="row">
		<div class="col-md-5 col-sm-5">
		{this.renderSearchForm()}
	        {this.renderSearchResults()}
	        </div>
		</div>
		<div class="row">
		<div class="col-sm-4 col-md-3 sidebar">
		<h4>Classes</h4>
		<div class="tree">
		{this.renderTree(ontology.classes)}
	        </div>
		<h4>Object Properties</h4>
		<div class="tree properties">
		{this.renderObjectProperties(ontology.properties)}
	        </div>
	        </div><div class="col-sm-8 col-md-9 main">
		<h1>{ontology.acronym} - {ontology.name}</h1>
		<h5>{ontology.description}</h5>
		{this.renderTabs()}
	        {this.renderCurrentTab()}
	        </div>
		</div>
	</div>
	);
    }
}

let HashRouter = ReactRouterDOM.HashRouter;
let Route = ReactRouterDOM.Route;
ReactDOM.render(
    <HashRouter>
	<div>
	<Route path="/:tab?/:owlClass?/:query?/" render={(routeProps) => <Ontology {...routeProps} ontology={window.ontology} />} />
        </div>
    </HashRouter>,
    window.react_mount
);
