class Ontology extends React.Component {

    constructor(props) {
	super(props);
	var classesMap = new Map();
	var classes = props.ontology.classes;
	for (var i = 0; i < classes.length; i++) {
	    classesMap.set(classes[i].owlClass, classes[i]); 
	}
	var currentTab = 'Overview';
	this.state = {
	    ontology: props.ontology,
	    classesMap: classesMap,
	    tabs: [
		'Overview', 'Browse', 'DLQuery',
		// 'Visualise', 'PubMed', 'Data', 'SPARQL',
		'Download'],
	    currentTab: currentTab,
	    selectedClass: null,
	    dlQuery: null,
	    dlResults: [],
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
		fetch('/api/backend?script=findRoot.groovy&query='
		      + encodeURIComponent(owlClass) + '&ontology='
		      + that.state.ontology.acronym)
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
		    fetch('/api/backend?script=findRoot.groovy&query='
			  + encodeURIComponent(owlClass) + '&ontology='
			  + this.state.ontology.acronym)
		    .then((response) => response.json())
		);
	    }
	    queries.push(
		fetch('/api/backend?script=runQuery.groovy&type=' + params.query
		      + '&direct=true&query=' + encodeURIComponent(owlClass)
		      + '&ontology=' + this.state.ontology.acronym)
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
	if (tab === this.state.currentTab) {
	    activeClass = 'active';
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

    renderBrowse() {
	const obj = this.state.selectedClass;
	if (obj == null) {
	    return (
		<div> Please select an ontology class. </div>
	    );
	}
	const ignoreFields = new Set([
	    'first_label',
	    'remainder',
	    'collapsed',
	    'children'
	]);
	
	const data = Object.keys(obj).filter(
	    (item) => !ignoreFields.has(item)).map(
		(item) => [item, obj[item].toString()]);
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

    renderDLQueryButtons() {
	const obj = this.state.selectedClass;
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
		    <a href={'#/DLQuery/' + encodeURIComponent(obj.owlClass) + '/' + item[0]}> { item[1] } </a>
		    </li>
	    );	    
	});

	return (
		<ul class="nav nav-pills">{ content }</ul>
	);
    }

    renderDLQuery() {
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
	const dlResults = this.state.dlResults;
	
	const content = dlResults.map(
	    (item) =>
		<tr>
		<td><a href={'#/Browse/' + encodeURIComponent(item.owlClass)}>{ item.owlClass }</a></td>
		<td>{ item.label }</td>
		<td>{ item.definition }</td>
		</tr>
	);
	return (
	    <div>
		{ this.renderDLQueryButtons() }
		<table class="table table-hover">
		<thead>{ header }</thead>
		<tbody>
		{ content }
	        </tbody>
		</table>
	    </div>
	);
    }

    renderSPARQL() {
	return (
	    <h2>Not yet implemented!</h2>
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
	const renders = [
	    this.renderOverview(),
	    this.renderBrowse(),
	    this.renderDLQuery(),
	    this.renderDownload()];
	for (var i = 0; i < renders.length; i++) {
	    if (this.state.currentTab == this.state.tabs[i]) {
		return renders[i];
	    }
	}
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
	const content = nodes.map(
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
	    var obj = classesMap.get(owlClass);
	    state.selectedClass = obj;
	    if (!('children' in obj)) {
		fetch(
		    '/api/backend?script=runQuery.groovy&type=subclass&direct=true&query='
			+ encodeURIComponent(obj.owlClass) + '&ontology=' + obj.ontologyURI)
		    .then(function(response){
			return response.json();
		    })
		    .then(function(data) {
			console.log(data);
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
	} else if (currentTab == 'DLQuery' && params.owlClass !== undefined && params.query !== undefined) {
	    const owlClass = decodeURIComponent(params.owlClass);
	    var queries = [];
	    const dlQuery = params.query;
	    fetch('/api/backend?script=runQuery.groovy&type=' + params.query
		  + '&direct=true&query=' + encodeURIComponent(owlClass)
		  + '&ontology=' + this.state.ontology.acronym)
	    .then((response) => response.json())
	    .then(function(data) {
		var dlResults = [];
		state.dlResults = data.result;
		state.dlQuery = dlQuery
		that.setState(state);
	    });
	} else {
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
    
    render() {
	const ontology = this.state.ontology;
	return (
	<div class="row">
		<div class="col-sm-4 col-md-3 sidebar">
		<div class="tree">
		{this.renderTree(ontology.classes)}
	        </div>
	    </div><div class="col-sm-8 col-md-9 main">
		<h1>{ontology.acronym} - {ontology.name}</h1>
		<h5>{ontology.description}</h5>
		{this.renderTabs()}
	        {this.renderCurrentTab()}
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
