
/* result dialog */

var result_dialog = document.getElementById('result');
var result_close_button = document.getElementById("result-close-button");
var result_close_img = document.getElementById("result-close-img");

result_close_button.addEventListener("click", () => {
  document.getElementById("result").close();
});

result_close_img.addEventListener("click", () => {
  document.getElementById("result").close();
});

/* process input metadata */

function processRecord() {

	console.clear();
	
	var xml = document.getElementById('input_record').value;
	
	if (!metaDisplayProcessor.initialize({
			record_as_text: xml
		})) {
		return;
	}
	
	showDisplayMetadata(false, 'html');
}

function reprocessRecord() {

	console.clear();
	
	var lang = document.getElementById('lang').value;
	
	var mode = document.getElementById('mode').value;

	var format = document.getElementById('format').value;

	if (!metaDisplayProcessor.reinitialize({
			lang: lang,
			mode: mode,
			format: format
		})) {
		return;
	}
	
	var suppressNoInfo = document.getElementById('no-info').value == 'hide' ? true : false;
	
	showDisplayMetadata(suppressNoInfo, format);
}

function showDisplayMetadata(suppressNoInfo, output_format) {

	// reset the result pane
	var result_field = document.getElementById('result-body');
		result_field.textContent = '';
	
	var result;
	
	if (output_format === 'html') {
		result = document.createElement('div');
		result.classList.add('grid');
	}
	
	else {
		result = '{';
	}
	
	// 3.1 Ways of reading
	
	var ways_result = metaDisplayProcessor.processWaysOfReading();
	
	if (ways_result.hasMetadata || !suppressNoInfo) {
	
		var id = 'ways-of-reading';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, ways_result.display);
		}
		else {
			result += formatJSON(id, hd, ways_result.display);
		}
	}
	
	// 3.2 Conformance
	
	var conf_result = metaDisplayProcessor.processConformance();
	
	if (conf_result.hasMetadata || !suppressNoInfo) {
		var id = 'conformance';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, conf_result.display);
		}
		else {
			result += "," + formatJSON(id, hd, conf_result.display);
		}
	}
	
	// 3.3 Navigation
	
	var nav_result = metaDisplayProcessor.processNavigation();
	
	if (nav_result.hasMetadata || !suppressNoInfo) {
	
		var id = 'navigation';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, nav_result.display);
		}
		else {
			result += "," + formatJSON(id,hd, nav_result.display);
		}
	}
	
	// 3.4 Rich content
	
	var rc_result = metaDisplayProcessor.processRichContent();
	
	if (rc_result.hasMetadata || !suppressNoInfo) {
	
		var id = 'rich-content';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, rc_result.display);
		}
		else {
			result += "," + formatJSON(id, hd, rc_result.display);
		}
	}
	
	// 3.5 Hazards
	
	var hazard_result = metaDisplayProcessor.processHazards();
	
	if (hazard_result.hasMetadata || !suppressNoInfo) {
	
		var id = 'hazards';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, hazard_result.display);
		}
		else {
			result += "," + formatJSON(id, hd, hazard_result.display);
		}
	}
	
	// 3.6 Accessibility summary
	
	var sum_result = metaDisplayProcessor.processAccessibilitySummary();
	
	if (sum_result.hasMetadata || !suppressNoInfo) {
	
		var id = 'accessibility-summary';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, sum_result.display);
		}
		else {
			result += "," + formatJSON(id, hd, sum_result.display);
		}
	}
	
	// 3.7 Legal considerations
	
	var legal_result = metaDisplayProcessor.processLegal();
	
	if (legal_result.hasMetadata || !suppressNoInfo) {
	
		var id = 'legal-considerations';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, legal_result.display);
		}
		else {
			result += "," + formatJSON(id, hd, legal_result.display);
		}
	}
	
	// 3.8 Additional accessibility information
	
	var aai_result = metaDisplayProcessor.processAdditionalA11yInfo();
	
	// additional information is never shown if there is nothing to display - it doesn't have a no information available string
	if (aai_result.hasMetadata) {
	
		var id = 'additional-accessibility-information';
		
		var hd = makeHeader(id, output_format);
		
		if (output_format === 'html') {
			formatHTML(result, hd, aai_result.display);
		}
		else {
			result += "," + formatJSON(id, hd, aai_result.display);
		}
	}
	
	
	if (result) {
		if (output_format === 'html') {
			result_field.appendChild(result);
		}
		else {
			var warning = document.createElement('p');
			var bold = document.createElement('strong');
				bold.appendChild(document.createTextNode('CAUTION: The following JSON output is experimental and subject to change at any time.'));
			warning.appendChild(bold);
			result_field.appendChild(warning);
			
			var pre = document.createElement('pre');
				pre.innerHTML = result + '\n}';
			result_field.appendChild(pre);
		}
		result_dialog.showModal();
	}
}



/* common header and explainer dialog */

function makeHeader(id, format) {

	var hd_str = metaDisplayProcessor.getHeader(id, '');
	
	if (format === 'json') {
		return JSON.stringify(hd_str);
	}
	
	else {
		var hd_block = document.createElement('div');
			hd_block.classList.add('grid-hd');
		
		var hd = document.createElement('h3');
			hd.appendChild(document.createTextNode(hd_str));
		hd_block.appendChild(hd);
		
		// if (expl_id) {
		// 	hd_block.appendChild(writeExplainerLink(expl_id));
		// }
		
		return hd_block;
	}
}


function formatHTML(result, hd, display) {
	result.appendChild(hd);
	display.classList.add('grid-body');
	result.appendChild(display);
}


function formatJSON(id, hd, statements) {
	return '\n\t"' + id + '": {\n\t\t"title": ' + hd + ',\n\t\t"statements": ' + statements + '\n\t}';
}


function writeExplainerLink(id) {
	var a = document.createElement('a');
		a.href = '#';
		a.classList.add('explainer-link');
		a.onclick = function () { showExplainer(id); return false; }
		a.title = 'Show explainer for this field';
	
	var img = document.createElement('img');
		img.src = 'graphics/info.png';
		img.alt = 'Show explainer for this field';
		img.onmouseover = function () { this.src = 'graphics/info_hover.png' }
		img.onmouseout = function () { this.src = 'graphics/info.png' }
	
	a.appendChild(img);
	
	return a;
}

var explainer_dialog = document.getElementById("explainer");

function showExplainer(id) {
	var expl_body = document.getElementById("explainer-body");
		expl_body.innerHTML = document.getElementById(id).innerHTML;
	explainer_dialog.showModal();
}

var explainer_close_button = document.getElementById("explainer-close-button");
var explainer_close_img = document.getElementById("explainer-close-img");

explainer_close_button.addEventListener('click', () => {
  explainer_dialog.close();
});

explainer_close_img.addEventListener('click', () => {
  explainer_dialog.close();
});


/* record selection */

var sel_dialog = document.getElementById('selectRecord');

function selectRecord() {
	sel_dialog.showModal();
}

var selectRecord_close_button = document.getElementById("selectRecord-close-button");
var selectRecord_close_img = document.getElementById("selectRecord-close-img");

selectRecord_close_button.addEventListener('click', () => {
  sel_dialog.close();
});

selectRecord_close_img.addEventListener('click', () => {
  sel_dialog.close();
});


async function loadRecord(record_file) {

	const response = await fetch('./samples/' + record_file);
	
	const record = await response.text();
	
	document.getElementById('input_record').value = record;
	
	sel_dialog.close();

}
