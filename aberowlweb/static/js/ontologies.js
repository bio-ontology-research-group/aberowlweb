function TopicsList(props) {
    const topics = props.topics;
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

function OntologiesList(props) {
    const ontologies = props.ontologies;
    const content = ontologies.map(
	(ontology) =>
	<tr>
	    <td>
	      {ontology.id}
	      <TopicsList topics={ontology.topics} />
	    </td>
	    <td> <span class="label label-default">{ontology.status}</span></td>
	    <td> {ontology.name}</td>
	    <td> {ontology.description}</td>
	</tr>
    );
    return (
	<table class="table table-stripped table-ontologies">
	  <th>Acronym</th>
	  <th>Status</th>
	  <th>Name</th>
	  <th>Description</th>
	  {content}
	</table>
    );
}

ReactDOM.render(
    <OntologiesList ontologies={window.ontoList} />,
    window.react_mount
);
