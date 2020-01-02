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
		<br/>
		<input class="form-control" type="text" value={this.props.filterValue} onChange={(e) => this.filterChange(e)} placeholder="Search"/>
	    </form>
	);
    }

    filterChange(e) {
	var v = e.target.value;
	this.setState({filterValue: v, page: 1});
	if (this.props.data !== undefined) {
	    const filteredRows = this.props.data.rows.filter(
		function(items) {
		    var keys = v.split(" ");
		    for (var key of keys) {
			var i = items.length - 1;
			if (items[i].indexOf(key) != -1) return true;
		    }
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
	    (items) => this.renderRow(items.slice(0, items.length - 1))
	);
	return (
	    <div class="container">
		<div class="row">
		    <div class="col-md-6">
			{this.renderFilter()}
		    </div><div class="col-md-6">
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

class DLResultTab extends React.Component {

	constructor(props) {
		super(props);
		var headers = props.headers ? props.headers : []
		var dlQuery = props.dlQuery ? props.dlQuery : null
		var query = props.query ? props.query : null
		this.state = {
			dlQuery: dlQuery,
			query: query,
			classes: [],
			total: null,
			per_page: 10,
			current_page: 1,
			headers:headers
		}
	}
  
  
	componentDidMount() {
	  this.executeDLQuery(1);
	}

	componentDidUpdate(props) {
		if (props.dlQuery !== this.props.dlQuery || props.query !== this.props.query) {
			this.setState({
				dlQuery: this.props.dlQuery,
				query: this.props.query
			});
			this.executeDLQuery(1, this.props.dlQuery, this.props.query)
		}
		
	}
  
	executeDLQuery(pageNumber, dlQuery, query) {
		var that = this;
		const response = fetch(`/api/dlquery?type=${dlQuery ? dlQuery : this.state.dlQuery}&labels=true&query=${encodeURIComponent(query ? query : this.state.query)}&offset=${pageNumber}`)
		.then(function(response){ return response.json(); })
		.then(function(data) {
			that.setState({
				classes: data.result,
				total: data.total,
				per_page: 10,
				current_page: pageNumber
			});
		});  
	}
  
	renderRow(items) {
	const cells = items.map(
		(item) => <td> {item} </td>);
	return (<tr> {cells} </tr>);
	}
  
	render() {
		let classes, renderPageNumbers;
		var n = Math.ceil(this.state.total/ this.state.per_page);
		const pageNumbers = [];
		if (this.state.total !== null) {
			for (var i = this.state.current_page - 2; i <= this.state.current_page + 2; i++) {
				if (i >= 1 && i <= n) {
					pageNumbers.push(i);
				}
			}
	
	
			renderPageNumbers = pageNumbers.map(number => {
			let classes = this.state.current_page === number ? 'active' : '';
	
			return (
				<span key={number} className={classes} onClick={() => this.executeDLQuery(number)}>{number}</span>
			);
			});
		}
		const paginator = (
			<div className={'serv-page  pull-right'}>
				<span class='first' onClick={() => this.executeDLQuery(this.state.current_page > 1 ? (this.state.current_page - 1): 1)}>&laquo;</span>
				{renderPageNumbers}
				<span class='last' onClick={() => this.executeDLQuery(this.state.current_page < n ? (this.state.current_page + 1): n)}>&raquo;</span>
			</div>
		);

		const header = this.state.headers.map((item) => <th> {item} </th>);
		

		if (this.state.classes != null) {
			classes = this.state.classes.map(item => {
				const onto = (<a href={'/ontology/' + item.ontology }> { item.ontology } </a>);
				const owlClass = (
					<a href={'/ontology/' + item.ontology + '/#/Browse/' + encodeURIComponent(item.owlClass)}>
					{item.label + '(' + item.owlClass + ')'}
					</a>
				);
				if (!item.definition) item.definition = '';
				var filterBy = item.ontology + item.label + item.definition;
				return (
					<tr>
						<td>{onto}</td>
						<td>{owlClass}</td>
						<td>{item.definition}</td>
						<td>{filterBy}</td>
					</tr>
			  	)
			}); 
		}
	  	return (
			<div class="container">
			<div class="row">
				<div class="col-md-8">
				</div>
				<div class="col-md-4">
				{paginator}
				</div>
			</div>
			<table class="table table-striped">
				<thead> {header} </thead>
				<tbody> {classes} </tbody>
			</table>
			<div class="row">
				<div class="col-md-8">
				</div>
				<div class="col-md-4">
				{paginator}
				</div>
			</div>
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
	    dlQuery: 'subeq',
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
		<input autofocus='' class="form-control input-lg" type="text" value={this.state.inputQuery} onChange={(e) => this.queryChange(e)} placeholder="Search"/>
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
	var query = newProps.match.params.query;
	if (query !== undefined && query != this.state.query) {
	    query = decodeURIComponent(query);
	    this.setState({query: query});
	    this.executeQuery(query);
	}
	var tab = newProps.match.params.tab;
	var page = newProps.match.params.page;
	if (page !== undefined) {
	    this.setState({page: page});
	} else {
	    this.setState({page: 1});
	}
	if (tab !== undefined) {
	    this.setState({currentTab: tab});
	} else {
	    this.setState({currentTab: 'Classes'});
	}
	
    }

    innerHTML(htmlString) {
	const html = {__html: htmlString};
	return (<span dangerouslySetInnerHTML={html}></span>);
    }

    executeDLQuery(query, dlQuery, page) {
	var that = this;
	fetch('/api/dlquery?type=' + dlQuery + '&labels=true&query=' + encodeURIComponent(query) + '&offset=' + page)
	    .then(function(response){ return response.json(); })
	    .then(function(data) {
		var dlQueryResults = {
		    headers: ['Ontology', 'OWL Class', 'Definition'], rows: [], total:0};
		if (data.status == 'ok') {
		    var rest = [];
		    for (var i = 0; i < data['result'].length; i++) {
			var item = data['result'][i];
			const onto = (<a href={'/ontology/' + item.ontology }> { item.ontology } </a>);
			const owlClass = (
			    <a href={'/ontology/' + item.ontology + '/#/Browse/' + encodeURIComponent(item.owlClass)}>
				{item.label + '(' + item.owlClass + ')'}
			    </a>
			);
			if (!item.definition) item.definition = '';
			var filterBy = item.ontology + item.label + item.definition;
			if (item.definition) {
			    dlQueryResults.rows.push([onto, owlClass, item.definition, filterBy]);
			} else {
			    rest.push([onto, owlClass, item.definition, filterBy]);
			}
		    }
		    for (var i = 0; i < rest.length; i++) {
			dlQueryResults.rows.push(rest[i]);
			}
			dlQueryResults['total'] = data['total']
		} else {
		    console.log('DLQuery', data);
		}
		var results = that.state.results;
		results['DLQuery'] = dlQueryResults;
		that.setState({results: results});
	    });
    }


    executeQuery(query) {
	this.setState({inputQuery: query});
	var that = this;
	Promise.all([
	    fetch('/api/class/_find?query=' + encodeURIComponent(query))
	    .then(function(response){
		return response.json();
	    }),
	    fetch('/api/ontology/_find?query=' + encodeURIComponent(query))
	    .then(function(response){
		return response.json();
	    }),
	]).then(function(data) {
	
	    var classes = {
		headers: ['Class', 'Definition', 'Ontology'], rows: []};
	    var rest = [];
	    for (var i in data[0]) {
		var term = data[0][i][0];
		var res = data[0][i][1];
		var ontos = [];
		if (!res[0].definition) res[0].definition = '';
		var definition = that.innerHTML(res[0].definition);
		var iri = res[0].owlClass;
		var label = res[0].label[0] + ' (' + iri + ')';
		var filterBy = term + res[0].definition;
		
		for (var i = 0; i < res.length; i++) {
		    const iri = '<' + res[i].class + '>';
		    ontos.push([res[i].ontology, encodeURIComponent(iri)]);
		    filterBy += res[i].ontology;
		}
		var ontos = ontos.map(function(onto) {
		    return (
			    <a href={'/ontology/' + onto[0] + '/#/Browse/' + onto[1]}> {onto[0]} </a>
		    );
		});
		if (res[0].definition) {
		    classes.rows.push([label, definition, ontos, filterBy]);
		} else {
		    rest.push([label, definition, ontos, filterBy]);
		}
	    }

	    for(var i = 0; i < rest.length; i++) {
		classes.rows.push(rest[i]);
	    }

	    var ontologies = {
		headers: ['ID', 'Name', 'Description'], rows: [] };
	    for (var i = 0; i < data[1].length; i++) {
		var item = data[1][i];
		var filterBy = item.ontology + item.name + item.description;
		const onto = (<a href={'/ontology/' + item.ontology }> { item.ontology } </a>);
		ontologies.rows.push([onto, item.name, item.description, filterBy])
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

	this.executeDLQuery(query, 'subeq', 1);
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
			var total = that.state.results[tab].total ? that.state.results[tab].total : that.state.results[tab].rows.length;
		    return [tab, total];
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

    renderDLQueryButtons() {
	const buttons = [
	    ['subclass', 'Subclasses'],
	    ['subeq', 'Sub and Equivalent'],
	    ['equivalent', 'Equivalent'],
	    ['superclass', 'Superclasses'],
	    ['supeq', 'Super and Equivalent']
	];

	var that = this;
	var dlQuery = this.state.dlQuery;
	const content = buttons.map(function(item) {
	    var activeClass = '';
	    if (dlQuery == item[0]) activeClass = 'active';
	    return (
		    <li role="presentation" className={ activeClass }>
		    <a href='#' onClick={(e) => that.handleDLQueryClick(e, item[0])}> { item[1] } </a>
		    </li>
	    );	    
	});

	return (
		<ul class="nav nav-pills">{ content }</ul>
	);
    }

    handleDLQueryClick(e, dlQuery) {
	e.preventDefault();
	this.setState({dlQuery: dlQuery});
    }

    renderQueryResults() {
	const currentTab = this.state.currentTab;
	if (this.state.results[currentTab] !== undefined) {
	    const results = this.state.results[currentTab];
	    const page = this.state.page;
	    const rootURI = '#/' + this.state.query + '/' + currentTab + '/';
		var dlQueryButtons = (<div></div>);
		var resultsTab=(<div></div>)
	    if (currentTab == 'DLQuery') {
			dlQueryButtons = this.renderDLQueryButtons();
			resultsTab = (<DLResultTab dlQuery={this.state.dlQuery} query={this.state.query} headers={results.headers}/>)
	    } else {
			resultsTab = (<ResultsTable data={results} page={page} rootURI={rootURI} pageFunction={this.executeDLQuery}/>)
		}
	    return (
		    <div class="row">
		    {this.renderResultTabs()}
		    {dlQueryButtons}
			<br/>
		    {resultsTab}
		    </div>
	    );
	}
	return (<div class="row"></div>);
    }

    render() {
	return (
	<div class="container">
	    <h1 align="center"><span>AberOWL ontology repository and semantic search engine</span></h1>
	    <div class="row">
	        <p>
		    Type any term or phrase to search the AberOWL ontology
		    repository for a class with label (try <a href="#/pancreas">pancreas</a>), 
			class description containing searched phrase or part of it (try <a href="#/sugar binding go" >sugar binding GO</a>),
		    using class OBO ID (try <a href="#/PATO:0001234">PATO:0001234</a>),
		    for ontologies by acronym (try  <a href="#/ECO/Ontologies">ECO</a>) or 
			by phrase part of ontology description (try <a href="#/integrated upper ontology/Ontologies">integrated upper ontology</a>,
		     <a href="#/infectious disease/Ontologies">infectious disease</a>,
		     or <a href="#/pathology/Ontologies">pathology</a>),
		    or perform a Description Logic query
		    (try <a href="#/'part of' some 'apoptotic process'/DLQuery">
		     'part of' some 'apoptotic process'</a> ):
	        </p>
	    </div>
	    <br/>
	    {this.renderQueryForm()}
	    <br/>
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
