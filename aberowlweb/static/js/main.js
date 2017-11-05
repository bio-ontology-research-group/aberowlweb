class ResultsTable extends React.Component {

    constructor(props) {
	super(props);
	var page = 1;
	if ('page' in props && props.page != undefined) {
	    page = parseInt(props.page);
	}
	var rows = [];
	var headers = [];
	if (props.data !== undefined) {
	    rows = props.data.rows.slice();
	    headers = props.data.headers;
	}
	this.state = {
	    page: page,
	    paginateBy: 10,
	    rows: rows,
	    headers: headers,
	    filterValue: '',
	};
    }

    componentWillReceiveProps(newProps) {
	var state = {}
	if (newProps.page !== undefined) {
	    state.page = parseInt(newProps.page);
	}

	if (this.props.data != newProps.data) {
	    state.page = 1;
	    state.headers = newProps.data.headers;
	    state.rows = newProps.data.rows.slice();
	    state.filterValue = '';
	}
	this.setState(state);
    }

    renderPageButton(page) {
	var activeClass = '';
	if (page == this.state.page) {
	    activeClass = 'active';
	}
	return (
		<li className={activeClass}>
		<a href={this.props.rootURI + page}>{page}</a>
		</li>
	);
    }

    renderPaginator() {
	var n = Math.ceil(this.state.rows.length / this.state.paginateBy);
	var page = this.state.page;
	var prevPage = page - 1 < 1 ? 1 : page - 1;
	var nextPage = page + 1 > n ? n : page + 1;
	var pages = Array();
	for (var i = page - 2; i <= page + 2; i++) {
	    if (i >= 1 && i <= n) {
		pages.push(i);
	    }
	}
	const content = pages.map(
	    (i) => this.renderPageButton(i));
	return (
	    <nav aria-label="Page navigation" class="pull-right">
	      <ul class="pagination">
		<li>
		<a href={this.props.rootURI + prevPage} aria-label="Previous">
		    <span aria-hidden="true">&laquo;</span>
		  </a>
		</li>
		{content}
		<li>
		<a href={this.props.rootURI + nextPage} aria-label="Next">
		    <span aria-hidden="true">&raquo;</span>
		  </a>
		</li>
	      </ul>
	    </nav>
	);
    }

    renderFilter() {
	return (
	    <form class="form">
		<input class="form-control" type="text" value={this.props.filterValue} onChange={(e) => this.filterChange(e)} placeholder="Search by topic"/>
	    </form>
	);
    }

    filterChange(e) {
	var v = e.target.value;
	this.setState({filterValue: v, page: 1});
	if (this.props.data !== undefined) {
	    const filteredRows = this.props.data.rows.filter(
		function(items) {
		    for(var i = 0; i < items.length; i++) {
			if (items[i] != null && (typeof items[i] === 'string' || items[i] instanceof String) && items[i].indexOf(v) != -1) return true;
		    }
		    return false;
		}
	    );
	    this.setState({rows: filteredRows});
	}
    }

    renderRow(items) {
	const cells = items.map(
	    (item) => <td> {item} </td>);
	return (<tr> {cells} </tr>);
    }
    
    render() {
	var paginateBy = this.state.paginateBy;
	var page = this.state.page;
	const rows = this.state.rows.slice(
	    (page - 1) * paginateBy, page * paginateBy);
	const header = this.state.headers.map(
	    (item) => <th> {item} </th>);
	const content = rows.map(
	    (items) => this.renderRow(items)
	);
	return (
	    <div class="row">
		<div class="row">
		    <div class="col-md-6">
			{this.renderFilter()}
		    </div>
		    <div class="col-md-6">
			{this.renderPaginator()}
		    </div>
		</div>
		<table class="table table-striped">
		    <thead> {header} </thead>
		    <tbody> {content} </tbody>
		</table>
		{this.renderPaginator()}
	    </div>
	);
    }
}


class Main extends React.Component {

    constructor(props) {
	super(props);
	var query = props.match.params.query;
	var currentTab = props.match.params.tab;
	const resultTabs = ['Classes', 'Ontologies', 'DLQuery'];
	this.state = {
	    query: query,
	    resultTabs: resultTabs,
	    currentTab: currentTab,
	    results: {},
	    inputQuery: '',
	};
    }

    componentWillMount() {
	if (this.state.query !== undefined) {
	    this.executeQuery(this.state.query);
	}
    }

    renderQueryForm() {
	return (

	    <div class="row">
		<div class="col-md-6 col-md-offset-3">
		<form class="form" onSubmit={(e) => this.handleSubmit(e)}>
		<div class="input-group input-group-lg">
		<input class="form-control input-lg" type="text" value={this.state.inputQuery} onChange={(e) => this.queryChange(e)} placeholder="Search"/>
		<span class="input-group-btn"><button type="submit" class="btn btn-lg">Query</button></span>
		</div>
		</form>
		</div>
		
	    </div>
	);
    }

    queryChange(e) {
	this.setState({inputQuery: e.target.value});
    }

    handleSubmit(e) {
	e.preventDefault();
	this.props.history.push('/' + encodeURIComponent(this.state.inputQuery));
    }

    componentWillReceiveProps(newProps) {
	console.log(newProps);
	var query = newProps.match.params.query;
	if (query !== undefined && query != this.state.query) {
	    console.log('Executing query');
	    query = decodeURIComponent(query);
	    this.setState({query: query});
	    this.executeQuery(query);
	}
	var tab = newProps.match.params.tab;
	var page = newProps.match.params.page;
	if (page !== undefined) {
	    this.setState({page: page});
	}
	if (tab !== undefined) {
	    this.setState({currentTab: tab});
	}
	
    }

    innerHTML(htmlString) {
	const html = {__html: htmlString};
	return (<span dangerouslySetInnerHTML={html}></span>);
    }

    executeQuery(query) {
	var that = this;

	Promise.all([
	    fetch('/api/querynames?query=' + encodeURIComponent(query))
	    .then(function(response){
		return response.json();
	    }),
	    fetch('/api/queryontologies?query=' + encodeURIComponent(query))
	    .then(function(response){
		return response.json();
	    }),
	]).then(function(data) {
	    console.log(data);
	
	    var classes = {
		headers: ['Class', 'Definition', 'Ontology'], rows: []};
	    for (var i in data[0]) {
		var term = data[0][i][0];
		var res = data[0][i][1];
		var ontos = [];
		const definition = that.innerHTML(res[0].definition);
		const iri = '<' + res[0].class + '>';
		const label = term + ' (' + iri + ')';
		
		for (var i = 0; i < res.length; i++) {
		    const iri = '<' + res[i].class + '>';
		    ontos.push([res[i].ontology, encodeURIComponent(iri)]);
		}
		var ontos = ontos.map(function(onto) {
		    return (
			    <a href={'/ontology/' + onto[0] + '/#/Browse/' + onto[1]}> {onto[0]} </a>
		    );
		});

		classes.rows.push([label, definition, ontos]);

	    }

	    var ontologies = {
		headers: ['ID', 'Name', 'Description'], rows: [] };
	    for (var i = 0; i < data[1].length; i++) {
		var item = data[1][i];
		const onto = (<a href={'/ontology/' + item.ontology }> { item.ontology } </a>);
		ontologies.rows.push([onto, item.name, item.description])
	    }

	    
	    var tab = that.state.currentTab;
	    if (tab === undefined) {
		tab = 'Classes';
	    }
	    var results = that.state.results;
	    results['Classes'] = classes;
	    results['Ontologies'] = ontologies;
	    that.setState({
		results: results,
		currentTab: tab
	    });
	});

	fetch('/api/backend?script=runQuery.groovy&type=subeq&labels=true&query=' + encodeURIComponent(query))
	    .then(function(response){ return response.json(); })
	    .then(function(data) {
		var dlQuery = {
		    headers: ['Ontology', 'OWL Class', 'Definition'], rows: []};
		for (var i = 0; i < data['result'].length; i++) {
		    var item = data['result'][i];
		    const onto = (<a href={'/ontology/' + item.ontologyURI }> { item.ontologyURI } </a>);
		    const owlClass = (
			<a href={'/ontology/' + item.ontologyURI + '/#/Browse/' + encodeURIComponent(item.owlClass)}>
			    {item.label + '(' + item.owlClass + ')'}
			</a>
		    );
		    dlQuery.rows.push([onto, owlClass, item.definition])
		}
		var results = that.state.results;
		results['DLQuery'] = dlQuery;
		that.setState({results: results});
	    });

    }

    renderTab(tab) {
	var activeClass = '';
	if (tab[0] == this.state.currentTab) {
	    activeClass = 'active';
	}
	
	return (
		<li role="presentation" className={activeClass}>
		<a href={'#/' + encodeURIComponent(this.state.query) + '/' + tab[0]}>{tab[0]}({tab[1]})</a>
		</li>
	);
    }
    
    renderResultTabs() {
	var that = this;
	const tabs = this.state.resultTabs.map(
	    function(tab){
		if (tab in that.state.results) {
		    return [tab, that.state.results[tab].rows.length];
		}
		return [tab, 0];
	    });
	
	const content = tabs.map(
	    (tab) => this.renderTab(tab)
	); 
	return (
	    <ul class="nav nav-tabs">
		{content}
	    </ul>
	);
    }

    renderQueryResults() {
	const currentTab = this.state.currentTab;
	if (this.state.results[currentTab] !== undefined) {
	    const results = this.state.results[currentTab];
	    const page = this.state.page;
	    const rootURI = '#/' + this.state.query + '/' + currentTab + '/';
	    return (
		    <div class="row">
		    {this.renderResultTabs()}
		    <ResultsTable data={results} page={page} rootURI={rootURI} />
		    </div>
	    );
	}
	return (<div class="row"></div>);
    }

    render() {
	return (
	<div class="row">
	    <h1 align="center"><span>AberOWL ontology repository and semantic search engine</span></h1>
	    <div class="row">
	        <p>
		    Type any term or phrase to search the AberOWL ontology
		    repository for a class that is described using the phrase
		    (try <a href="#/pancreas">pancreas</a>,
		     <a href="#/PATO:0001234">PATO:0001234</a>,
		     <a href="#/sugar binding go" >sugar binding GO</a>),
		    for ontologies that use the phrase in their description
		    (try  <a href="#/integrated upper ontology">integrated upper ontology</a>,
		     <a href="#/infectious disease">infectious disease</a>,
		     <a href="#/GFO">GFO</a> or <a href="#/pathology">pathology</a>),
		    or perform a Description Logic query across all ontologies in AberOWL
		    (try <a href="#/'part of' some 'apoptotic process' and regulates some 'apoptotic process'">
		     'part of' some 'apoptotic process' and regulates some 'apoptotic process'</a> ):
	        </p>
	    </div>
	    {this.renderQueryForm()}
	    {this.renderQueryResults()}
	</div>
	);
    }
}

let HashRouter = ReactRouterDOM.HashRouter;
let Route = ReactRouterDOM.Route;
ReactDOM.render(
    <HashRouter>
	<div>
	<Route path="/:query?/:tab?/:page?" render={(routeProps) => <Main {...routeProps} />} />
        </div>
    </HashRouter>,
    window.react_mount
);
