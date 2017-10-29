class TopicList extends React.Component {
    render() {
	const topics = this.props.topics;
	if (topics != null) {
            const content = topics.map(
		(topic) =>
		    <span class="label label-default aberowl-topic">{topic[1]}</span>
            );
            return (
	    <div>
		{content}
	    </div>
	    );
	}
	return (<div></div>);
     }
}

class OntologyList extends React.Component {

    constructor(props) {
	super(props);
	console.log(props);
	var page = 1;
	if (props.match.params.page != undefined) {
	    page = parseInt(props.match.params.page);
	}
	this.state = {
	    page: page,
	    paginateBy: 10,
	    ontologies: props.ontologies.slice(),
	    filterValue: ''
	};
    }

    renderPageButton(page) {
	var activeClass = '';
	if (page == this.state.page) {
	    activeClass = 'active';
	}
	return (
		<li className={activeClass}>
		<a href={'#/' + page}>{page}</a>
		</li>
	);
    }

    componentWillReceiveProps(newProps) {
	var page = parseInt(newProps.match.params.page);
	this.setState({
	    page: page,
	});
    }

    renderPaginator() {
	var n = Math.ceil(this.state.ontologies.length / this.state.paginateBy);
	var page = this.state.page;
	var prevPage = page - 1 < 1 ? 1 : page - 1;
	var nextPage = page + 1 > n ? n : page + 1;
	var pages = Array();
	for (var i = page - 2; i <= page + 2; i++) {
	    if (i >= 1 && i <= n) {
		pages.push(i);
	    }
	}
	const content = pages.map((i) =>
				  this.renderPageButton(i));
	return (
	    <nav aria-label="Page navigation" class="pull-right">
	      <ul class="pagination">
		<li>
		<a href={'#/' + prevPage} aria-label="Previous">
		    <span aria-hidden="true">&laquo;</span>
		  </a>
		</li>
		{content}
		<li>
		<a href={'#/' + nextPage} aria-label="Next">
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
		<input class="form-control" type="text" value={this.state.filterValue} onChange={(e) => this.filterChange(e)} placeholder="Search by topic"/>
	    </form>
	);
    }

    filterChange(e) {
	var v = e.target.value;
	this.setState({filterValue: v, page: 1});
	var s = v.toLowerCase();
	const ontologies = this.props.ontologies.filter(
	    function(ontology) {
		if (ontology.acronym.toLowerCase().indexOf(s) != -1)
		    return true;
		if (ontology.name.toLowerCase().indexOf(s) != -1)
		    return true;
		if (ontology.description !== undefined && ontology.description.indexOf(s) != -1)
		    return true;
		if (ontology.topics) {
		    for(var i = 0; i < ontology.topics.length; i++) {
			var topic = ontology.topics[i];
			if (topic[1].indexOf(v) != -1) return true;
		    }
		}
		return false;
	    }
	);
	this.setState({ontologies: ontologies});
    }
    
    render() {
	var paginateBy = this.state.paginateBy;
	var page = this.state.page;
	const ontologies = this.state.ontologies.slice(
	    (page - 1) * paginateBy, page * paginateBy);
	const content = ontologies.map(
	    (ontology) =>
		<div class="col-md-12">
		<h2>
		<a href={'/ontology/' + ontology.acronym}>{ontology.acronym} </a>
		 - { ontology.name }
		</h2>
		<p> {ontology.submission.description}</p>
		<span class="badge">{ontology.status}</span>
		<div class="pull-right"><TopicList topics={ ontology.topics }/></div>
		<hr class="col-md-12"/>
		</div>
	);
	return (
	    <div class="row">
	    <div class="row">
		<div class="col-md-6">
		{ this.renderFilter() }
	        </div>
	        <div class="col-md-6">
		{ this.renderPaginator() }
	        </div>
	        </div>
	    { content }
	    { this.renderPaginator() }
	    </div>
	);
    }
}

let HashRouter = ReactRouterDOM.HashRouter;
let Route = ReactRouterDOM.Route;
ReactDOM.render(
    <HashRouter>
	<div>
	<Route path="/:page?" render={(routeProps) => <OntologyList {...routeProps} ontologies={window.ontoList} />} />
        </div>
    </HashRouter>,
    window.react_mount
);
