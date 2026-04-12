
var xpath = {
	ways_of_reading: {
		all_textual_content_can_be_modified: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="displayTransformability"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="displayTransformability"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "36"]'
		},
		is_fixed_layout: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="rendition:layout" and normalize-space()="pre-paginated"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="rendition:layout" and normalize-space(@content)="pre-paginated"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormDetail[normalize-space() = "E201"]'
		},
		is_reflow: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormDetail[normalize-space() = "E200"]'
		},
		all_necessary_content_textual: {
			epub3: '/opf:package/opf:metadata/opf:meta[(@property="schema:accessMode" and normalize-space()="textual" and count(//opf:meta[@property="schema:accessMode"]) = 1) or (@property="schema:accessModeSufficient" and normalize-space()="textual")]',
			epub2: '/opf:package/opf:metadata/opf:meta[(@name="schema:accessMode" and normalize-space(@content)="textual" and count(//opf:meta[@name="schema:accessMode"]) = 1) or (@name="schema:accessModeSufficient" and normalize-space()="textual")]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "52"]'
		},
		audio_only_content: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessMode" and normalize-space() = "auditory" and count(//opf:meta[@property="schema:accessMode"]) = 1]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessMode" and normalize-space(@content) = "auditory" and count(//opf:meta[@name="schema:accessMode"]) = 1]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:PrimaryContentType = "01" or onix:ProductContentType = "01"]'
		},
		real_text: {
			epub3: null,
			epub2: null,
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:PrimaryContentType = "10" or onix:ProductContentType = "10"]'
		},
		some_sufficient_text: {
			epub3: '/opf:package/opf:metadata/opf:meta[(@property="schema:accessMode" and contains(normalize-space(), "textual")) or (@property="schema:accessModeSufficient" and contains(normalize-space(), "textual"))]',
			epub2: '/opf:package/opf:metadata/opf:meta[(@name="schema:accessMode" and contains(normalize-space(@content), "textual")) or (@name="schema:accessModeSufficient" and contains(normalize-space(@content), "textual"))]'
		},
		textual_alternatives: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and contains(" longDescription alternativeText describedMath transcript ", normalize-space())]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and contains(" longDescription alternativeText describedMath transcript ", normalize-space(@content))]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and (onix:ProductFormFeatureValue = "14" or onix:ProductFormFeatureValue = "15" or onix:ProductFormFeatureValue = "16")]'
		},
		transcripts: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormDetail[normalize-space() = "V212"]'
		},
		visual_only_content: {
			epub3: '/opf:package/opf:metadata/opf:meta[(@property="schema:accessMode" and normalize-space() = "visual" and count(//opf:meta[@property="schema:accessMode"]) = 1) and not(//opf:meta[@property="schema:accessModeSufficient" and contains(normalize-space(), "textual")])]',
			epub2: '/opf:package/opf:metadata/opf:meta[(@name="schema:accessMode" and normalize-space(@content) = "visual" and count(//opf:meta[@name="schema:accessMode"]) = 1) and not(//opf:meta[@name="schema:accessModeSufficient" and contains(normalize-space(@content), "textual")])]'
		},
		all_content_audio: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessModeSufficient" and normalize-space()="auditory"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessModeSufficient" and normalize-space(@content)="auditory"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "39"]'
		},
		all_content_pre_recorded: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "51"]'
		},
		synchronised_pre_recorded_audio: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="synchronizedAudioText"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="synchronizedAudioText"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "20"]'
		},
		synchronised_pre_recorded_audio_2: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormDetail[normalize-space() = "A305"]'
		},
		audiobook: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:PrimaryContentType = "01" or onix:ProductContentType = "01"]'
		},
		audio_content: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessMode" and normalize-space()="auditory"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessMode" and normalize-space(@content)="auditory"]'
		},
		non_textual_content_audio: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:PrimaryContentType = "21" or onix:PrimaryContentType = "22" or onix:ProductContentType = "21" or onix:ProductContentType = "22"]'
		},
		non_textual_content_audio_in_video: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:PrimaryContentType = "06" or onix:PrimaryContentType = "25" or onix:PrimaryContentType = "26" or onix:PrimaryContentType = "27" or onix:PrimaryContentType = "28" or onix:PrimaryContentType = "29" or onix:PrimaryContentType = "30" or onix:ProductContentType = "06" or onix:ProductContentType = "25" or onix:ProductContentType = "26" or onix:ProductContentType = "27" or onix:ProductContentType = "28" or onix:ProductContentType = "29" or onix:ProductContentType = "30"]'
		}
	},
	conformance: {
		epub10a: {
			epub3: '/opf:package/opf:metadata/opf:*[(@rel="dcterms:conformsTo" and @href="http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-a") or (@property="dcterms:conformsTo" and normalize-space() = "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-a")]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="dcterms:conformsTo" and normalize-space(@content)="http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-a"]'
		},
		epub10aa: {
			epub3: '/opf:package/opf:metadata/opf:*[(@rel="dcterms:conformsTo" and @href="http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aa") or (@property="dcterms:conformsTo" and normalize-space() = "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aa")]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="dcterms:conformsTo" and normalize-space(@content)="http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aa"]'
		},
		epub10aaa: {
			epub3: '/opf:package/opf:metadata/opf:*[(@rel="dcterms:conformsTo" and @href="http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aaa") or (@property="dcterms:conformsTo" and normalize-space() = "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aaa")]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="dcterms:conformsTo" and normalize-space(@content)="http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aaa"]'
		},
		conformance: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="dcterms:conformsTo" and contains(normalize-space(), "EPUB Accessibility 1.1 - WCAG 2.")]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="dcterms:conformsTo" and contains(normalize-space(@content), "EPUB Accessibility 1.1 - WCAG 2.")]/@content'
		},
		epub_accessibility_10_1: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "02"]'
		},
		epub_accessibility_10_2: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "03"]'
		},
		epub_accessibility_11: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "04"]'
		},
		wcag_20_1: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "80"]'
		},
		wcag_20_2: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "02"]'
		},
		wcag_20_3: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "03"]'
		},
		wcag_21: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "81"]'
		},
		wcag_22: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "82"]'
		},
		level_a_1: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "84"]'
		},
		level_a_2: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "02"]'
		},
		level_aa_1: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "85"]'
		},
		level_aa_2: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "03"]'
		},
		level_aaa: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "86"]'
		},
		lia_compliant: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "01"]'
		},
		certifier: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="a11y:certifiedBy" and (not(@refines) or substring(@refines,2)=//opf:*[(@rel="dcterms:conformsTo" and contains(@href, "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "EPUB Accessibility 1.1 - WCAG 2."))]/@id)]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="a11y:certifiedBy"]/@content',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "90"]/onix:ProductFormFeatureDescription'
		},
		certifier_credential: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="a11y:certifierCredential" and (not(@refines) or substring(@refines,2)=//opf:meta[@property="a11y:certifiedBy" and substring(@refines,2)=//opf:*[(@rel="dcterms:conformsTo" and contains(@href, "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "EPUB Accessibility 1.1 - WCAG 2."))]/@id]/@id)]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="a11y:certifierCredential"]/@content',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "93"]/onix:ProductFormFeatureDescription'
		},
		certification_date: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="dcterms:date" and substring(@refines,2)=//*[(@rel="dcterms:conformsTo" and contains(@href, "http://www.idpf.org/epub/a11y/")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "http://www.idpf.org/epub/a11y/")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "EPUB Accessibility 1.1"))]/@id]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="dcterms:date"]/@content',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "91"]/onix:ProductFormFeatureDescription'
		},
		certifier_report: {
			epub3: '/opf:package/opf:metadata/opf:*[@rel="a11y:certifierReport" and (not(@refines) or substring(@refines,2)=//opf:meta[@property="a11y:certifiedBy" and substring(@refines,2)=//opf:*[(@rel="dcterms:conformsTo" and contains(@href, "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-")) or (@property="dcterms:conformsTo" and contains(normalize-space(), "EPUB Accessibility 1.1 - WCAG 2."))]/@id]/@id)]/@href',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="a11y:certifierReport"]/@content',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "94"]/onix:ProductFormFeatureDescription'
		}
	},
	navigation: {
		table_of_contents_navigation: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="tableOfContents"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="tableOfContents"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "11"]'
		},
		index_navigation: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="index"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="index"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "12"]'
		},
		page_navigation: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="pageNavigation"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="pageNavigation"]'
		},
		print_equivalent_page_numbering: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "19"]'
		},
		next_previous_structural_navigation: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="structuralNavigation"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="structuralNavigation"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "29"]'
		}
	},
	rich_content: {
		contains_charts_diagrams: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessMode" and normalize-space()="chartOnVisual"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessMode" and normalize-space(@content)="chartOnVisual"]'
		},
		charts_diagrams_as_non_graphical_data: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "16"]'
		},
		full_alternative_textual_descriptions: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="longDescriptions"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="longDescriptions"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "15"]'
		},
		short_textual_alternative_images: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "14"]'
		},
		contains_chemical_formula: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessMode" and normalize-space()="chemOnVisual"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessMode" and normalize-space(@content)="chemOnVisual"]'
		},
		chemical_formula_as_latex: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="latex-chemistry"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="latex-chemistry"]'
		},
		chemical_formula_as_mathml: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="MathML-chemistry"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="MathML-chemistry"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "34"]'
		},
		contains_math_formula: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="describedMath"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="describedMath"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:DescriptiveDetail[onix:PrimaryContentType = "48" or onix:ContentType = "48"]'
		},
		math_formula_as_latex: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="latex"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="latex"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "35"]'
		},
		math_formula_as_mathml: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="MathML"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="MathML"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "17"]'
		},
		closed_captions: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="closedCaptions"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="closedCaptions"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:ProductFormDetail = "V210"]'
		},
		open_captions: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="openCaptions"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="openCaptions"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:ProductFormDetail = "V211"]'
		},
		transcript: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="transcript"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="transcript"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:ProductFormDetail = "V212"]'
		}
	},
	hazards: {
		no_hazards_or_warnings_confirmed: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="none"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="none"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "00"]'
		},
		flashing_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="flashing"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="flashing"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "13"]'
		},
		no_flashing_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="noFlashingHazard"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="noFlashingHazard"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "14"]'
		},
		unknown_flashing_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="unknownFlashingHazard"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="unknownFlashingHazard"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "24"]'
		},
		motion_simulation_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="motionSimulation"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="motionSimulation"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "17"]'
		},
		no_motion_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="noMotionSimulationHazard"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="noMotionSimulation"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "18"]'
		},
		unknown_motion_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="unknownMotionSimulationHazard"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="unknownMotionSimulationHazard"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "26"]'
		},
		sound_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="sound"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="sound"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "15"]'
		},
		no_sound_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="noSoundHazard"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="noSoundHazard"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "16"]'
		},
		unknown_sound_hazard: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="unknownSoundHazard"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="unknownSoundHazard"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "12" and onix:ProductFormFeatureValue = "25"]'
		},
		unknown_if_contains_hazards: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityHazard" and normalize-space()="unknown"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityHazard" and normalize-space(@content)="unknown"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "08"]'
		}
	},
	summary: {
		accessibility_summary: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilitySummary"][1]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilitySummary"][1]/@content',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "00"]/onix:ProductFormFeatureDescription'
		},
		lang_attribute_accessibility_summary: {
			epub3: '(/opf:package/opf:metadata/opf:meta[@property="schema:accessibilitySummary"][1]/@xml:lang | /opf:package/@xml:lang)[last()]',
			epub2: '(/opf:package/opf:metadata/opf:meta[@name="schema:accessibilitySummary"][1]/@xml:lang | /opf:package/@xml:lang)[last()]',
			onix: '(/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "00"]/onix:ProductFormFeatureDescription/@lang | /onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "00"]/onix:ProductFormFeatureDescription/ancestor::*/@lang)[last()]'
		},
		language_of_text: {
			epub3: '/opf:package/opf:metadata/dc:language[1]',
			epub2: '/opf:package/opf:metadata/dc:language[1]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:Language[onix:LanguageRole="01"]/onix:LanguageCode'
		},
		accessibility_addendum: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "92"]/onix:ProductFormFeatureDescription'
		},
		lang_attribute_accessibility_addendum: {
			onix: '(/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "92"]/onix:ProductFormFeatureDescription/@lang | /onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "92"]/onix:ProductFormFeatureDescription/ancestor::*/@lang)[last()]'
		},
		known_limited_accessibility: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "09"]/onix:ProductFormFeatureDescription'
		},
		lang_known_limited_accessibility: {
			onix: '(/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "09"]/onix:ProductFormFeatureDescription/@lang | /onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "09"]/onix:ProductFormFeatureDescription/ancestor::*/@lang)[last()]'
		},
		publisher_contact_for_accessibility: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "99"]/onix:ProductFormFeatureDescription'
		}
	},
	legal: {
		exemption: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="a11y:exemption"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="a11y:exemption"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and (onix:ProductFormFeatureValue = "75" or onix:ProductFormFeatureValue = "76" or onix:ProductFormFeatureValue = "77")]'
		}
	},
	add_info: {
		audio_descriptions: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="audioDescription"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="audioDescription"]'
		},
		braille: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="braille"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="braille"]'
		},
		tactile_graphic: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="tactileGraphic"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="tactileGraphic"]'
		},
		tactile_object: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="tactileObject"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="tactileObject"]'
		},
		dyslexia_readability: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "24"]'
		},
		sign_language: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="signLanguage"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="signLanguage"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:ProductFormDetail = "V213"]'
		},
		aria: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="aria"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="aria"]'
		},
		full_ruby_annotations: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="fullRubyAnnotations"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="fullRubyAnnotations"]'
		},
		text_to_speech_hinting: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="ttsMarkup"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="ttsMarkup"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "21"]'
		},
		high_contrast_between_foreground_and_background_audio: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="highContrastAudio"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="highContrastAudio"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "27"]'
		},
		without_background_sounds: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:ProductFormDetail = "A312"]'
		},
		high_contrast_between_text_and_background: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="highContrastDisplay"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="highContrastDisplay"]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "26"]'
		},
		ultra_high_contrast_between_text_and_background: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "37"]'
		},
		large_print:  {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="largePrint"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="largePrint"]'
		},
		color_not_sole_means_of_conveying_information: {
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail/onix:ProductFormFeature[onix:ProductFormFeatureType = "09" and onix:ProductFormFeatureValue = "25"]'
		},
		page_break_markers: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and (normalize-space()="pageBreakMarkers" or normalize-space()="printPageNumbers")]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and (normalize-space(@content)="pageBreakMarkers" or normalize-space(@content)="printPageNumbers")]',
			onix: '/onix:ONIXMessage/onix:Product/onix:DescriptiveDetail[onix:ProductFormDetail = "E205"]'
		},
		ruby_annotations: {
			epub3: '/opf:package/opf:metadata/opf:meta[@property="schema:accessibilityFeature" and normalize-space()="rubyAnnotations"]',
			epub2: '/opf:package/opf:metadata/opf:meta[@name="schema:accessibilityFeature" and normalize-space(@content)="rubyAnnotations"]'
		}
	}
};
