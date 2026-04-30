# 14 Critic flags from runs/20260430-164347/

All 14 flag reasons in full. Each row: obligation ID, Critic confidence, reviewed mappings, full reasoning text.


## EUAIA-OBL-007  ·  Critic confidence 0.86

**Reviewed mappings:** GOVERN-1.1, MANAGE-1.1, MAP-1.1

The GOVERN-1.1 and MAP-1.1 mappings are defensible: GOVERN-1.1 cleanly captures the need to understand and document a hard legal prohibition with narrow exceptions, and MAP-1.1's explicit text on context-specific laws and deployment settings aligns well with the obligation's conditional deployment logic. However, the MANAGE-1.1 mapping at 0.77 warrants flagging. MANAGE-1.1 is fundamentally about determining whether an AI system achieves its intended purposes and whether development/deployment should proceed in a general fitness-for-purpose sense. The Mapper's reasoning stretches this into a deployment-authorisation gate-keeping role that the control does not natively describe. The obligation's core concern is a near-absolute prohibition subject to procedurally authorised narrow exceptions — this is a legal compliance and access-control governance matter, not a system-performance determination. A stronger fit would have been GOVERN-1.4 ('risk management process and its outcomes are established through transparent policies, procedures, and other controls based on organizational risk priorities'), which more directly addresses the procedural controls and policy structures needed to operationalise the Article 5(2)–(7) authorisation conditions. GOVERN-1.3 ('processes, procedures, and practices are in place to determine the needed level of risk management activities based on the organization's risk tolerance') is also more aligned with the exception-triggering decision logic than MANAGE-1.1. The Mapper did not consider these alternatives. The MANAGE-1.1 reasoning, while not entirely implausible, leans on a re-characterisation of the control's purpose that a human reviewer should evaluate before this mapping ships.


## EUAIA-OBL-011  ·  Critic confidence 0.85

**Reviewed mappings:** GOVERN-1.1, GOVERN-6.1

GOVERN-1.1 at 0.88 is well-reasoned and defensible — the obligation is squarely a legal compliance duty and GOVERN-1.1 is the natural home for it. No issue there.

The GOVERN-6.1 mapping at 0.78 is more questionable and warrants human review. GOVERN-6.1 is specifically scoped to 'AI risks associated with third-party entities, including risks of infringement of a third party's intellectual property or other rights.' The Mapper's reasoning re-frames the obligation as being about third-party operator risk management in downstream deployment contexts, but the obligation itself is focused on the provider's own legal compliance duty under the AI Act for a dual-use system they place on the market — not on third-party supply chain or IP risks. The logic requires a conceptual leap (law enforcement/national security operators = third-party entities triggering GOVERN-6.1) that is not well-grounded in the control's text. A more natural second mapping might have been GOVERN-1.2 (integrating trustworthy AI characteristics into organizational policies and processes, which would directly support Act compliance operationalisation) or GOVERN-2.3 (executive accountability for risk decisions, relevant given the high-stakes dual-use nature). The Mapper's reasoning for GOVERN-6.1 leans on 'third-party deployment scenarios' framing that stretches the control beyond its evident intent. A human reviewer should assess whether GOVERN-6.1 adds meaningful coverage here or whether the second slot should be reconsidered.


## EUAIA-OBL-022  ·  Critic confidence 0.85

**Reviewed mappings:** GOVERN-1.1, MANAGE-4.1, MEASURE-2.8

All three mappings are defensible at a broad level but each has notable weaknesses that warrant human review before publication.

**GOVERN-1.1 (0.80):** The strongest of the three. Mapping a specific legal labelling obligation to the foundational 'legal and regulatory requirements are understood, managed, and documented' control is a standard and defensible catch-all. No objection here.

**MEASURE-2.8 (0.78):** The Mapper frames this as a transparency and accountability mapping, which is plausible. However, MEASURE-2.8 is oriented toward *examining and documenting* risks associated with transparency — it is a measurement/assessment activity. The obligation is an operational labelling duty (producing and affixing visible disclosure artefacts before dissemination), not a risk examination activity. MEASURE-2.8 addresses the analytical side of accountability risk, not the execution of disclosure actions. A stronger fit might be found in GOVERN-4.2 (documenting and communicating risks/impacts of AI technology more broadly, including disclosure practices) or GOVERN-1.2 (integrating trustworthy AI characteristics — including transparency — into organisational policies, procedures, and practices). Neither is the same as MEASURE-2.8, and the Mapper did not return either.

**MANAGE-4.1 (0.76):** The Mapper's reasoning acknowledges it leans on a broad reading — 'mechanisms for capturing and evaluating input from users' is being stretched to cover labelling/disclosure artefacts. MANAGE-4.1 is fundamentally about post-deployment monitoring, incident response, appeal/override, and change management. Labelling deep fakes before dissemination is a pre-dissemination operational control, not a monitoring or feedback capture mechanism. GOVERN-1.2 (integrating transparency characteristics into organisational processes/practices) or GOVERN-4.2 (documenting and communicating AI risks and impacts) would be a more direct fit for the operational disclosure duty. The Mapper's reasoning uses the phrase 'including disclosure mechanisms' which is not language found in MANAGE-4.1's subcategory text — a sign of hedging toward a familiar choice rather than a specific match.


## EUAIA-OBL-024  ·  Critic confidence 0.83

**Reviewed mappings:** GOVERN-1.1, MAP-1.1, MEASURE-2.8

Two of the three mappings are defensible at their stated confidence levels, but the MAP-1.1 mapping at 0.76 warrants scrutiny. The obligation is primarily a technical implementation duty — providers must embed design features and technical detection measures into the AI system itself to enable visible disclosure. MAP-1.1 concerns understanding and documenting intended purposes, context-specific laws, and deployment settings at the context-mapping stage. While it does reference 'context-specific laws,' the obligation goes well beyond contextual awareness: it mandates concrete, embedded technical measures (detection mechanisms, design features) that are operational rather than documentary. Using MAP-1.1 as a mapping here conflates legal-awareness documentation with a technical engineering requirement.

Moreover, the Mapper's reasoning for MAP-1.1 leans heavily on the phrase 'context-specific laws, norms and expectations' as if that single element makes MAP-1.1 a fit — language that reads as hedging toward a familiar catch-all rather than a substantive match. A stronger candidate the Mapper did not return is GOVERN-1.2 ('The characteristics of trustworthy AI are integrated into organizational policies, processes, procedures, and practices'), which more directly addresses embedding trustworthiness properties — including transparency — into system design, or MEASURE-2.9 ('The AI model is explained, validated, and documented, and AI system output is interpreted within its context … to inform responsible use and governance'), which more directly addresses interpretability and disclosure of AI outputs. A human reviewer should assess whether MAP-1.1 adds meaningful coverage beyond GOVERN-1.1 and MEASURE-2.8 for this obligation, or whether it should be replaced or dropped.


## EUAIA-OBL-026  ·  Critic confidence 0.83

**Reviewed mappings:** GOVERN-1.1, MAP-1.1, MEASURE-2.9

The first two mappings are defensible. GOVERN-1.1 is a natural anchor for a direct legal prohibition that must be understood, managed, and documented. MAP-1.1 is a reasonable fit for assessing whether deployment context and intended use could give rise to behaviour-distorting effects, as it covers context-specific laws, user impacts, and deployment settings.

However, the MEASURE-2.9 mapping at 0.77 warrants scrutiny. MEASURE-2.9 concerns explaining, validating, and interpreting AI model outputs within context to inform responsible use and governance — it is primarily an explainability/interpretability control. The Mapper's reasoning stretches this by treating model explanation as a proxy for demonstrating the *absence* of manipulative mechanisms, which is a conceptually distinct activity. The obligation's core evidence requirement is demonstrating that the system does not deploy techniques capable of materially distorting behaviour — a safety and risk-evaluation concern rather than an output-interpretation concern. A stronger candidate that the Mapper did not return is MEASURE-2.8 ('Risks associated with transparency and accountability... are examined and documented'), which more directly addresses the documentation of risks arising from how the system influences or affects users, and is closer to the transparency dimension of the prohibition. MEASURE-2.6 (safety risk evaluation) is also a plausible fit given the 'materially distorting behaviour' harm threshold. The Mapper's reasoning relies on treating explainability as equivalent to behavioural-manipulation audit, which is a related-but-distinct concern, and the hedge in the reasoning ('directly served by') is not fully supported by the subcategory text. A human reviewer should assess whether MEASURE-2.9 is the most defensible MEASURE-function mapping or whether a different subcategory better addresses the technical documentation evidence requirement.


## EUAIA-OBL-030  ·  Critic confidence 0.82

**Reviewed mappings:** GOVERN-1.1, MAP-1.1, MEASURE-2.9

The MAP-1.1 mapping at 0.78 confidence warrants scrutiny. The obligation's core data-related requirement is not merely about understanding deployment context and documenting intended use — it is specifically about demonstrating that only contextually scoped data is processed for social scoring purposes, with evidence of data type and source restrictions. MAP-1.1 addresses context documentation at a high level, but the Mapper's reasoning stretches it to cover a data minimisation and scope-restriction obligation it does not squarely address. MAP-1.6 ('System requirements are elicited from and understood by relevant AI actors; design decisions take socio-technical implications into account to address AI risks') or MAP-2.3 ('Scientific integrity and TEVV considerations are identified and documented, including those related to data collection and selection — availability, representativeness, suitability') would have been stronger fits for the data-types-and-sources documentation requirement. MAP-2.3 in particular directly calls out 'data collection and selection' documentation, which aligns more tightly with the obligation's demand for transparency about data types, data sources, and contextual scope of data processed. The Mapper's reasoning for MAP-1.1 leans on 'broadly applicable' language ('directly supports the contextual data scope justification') without acknowledging that MAP-1.1 is fundamentally a system-purpose and deployment-context scoping control, not a data minimisation or data-source documentation control. The GOVERN-1.1 (0.85) and MEASURE-2.9 (0.82) mappings are defensible and do not raise concerns.


## EUAIA-OBL-042  ·  Critic confidence 0.87

**Reviewed mappings:** GOVERN-1.1, GOVERN-3.2, MANAGE-4.1

All three mappings are defensible at a surface level, but two of the three low-confidence entries warrant scrutiny:

**GOVERN-3.2 (0.76):** The Mapper's reasoning is partially on target — Article 5(2)–(7) does involve human oversight structures and prior-authorisation workflows. However, GOVERN-3.2's primary focus is on *role differentiation in human-AI configurations*, which is a narrower organisational-design concern. The obligation's core duty is compliance with a specific set of legal conditions and safeguards for a prohibited-category use case that has been exceptionally authorised. The reasoning's hedge ('directly operationalises through defined human-AI oversight policies') leans toward a related-but-distinct concern. A stronger candidate from the catalogue for the authorisation and oversight procedural dimension would be GOVERN-1.4 ('risk management process and its outcomes are established through transparent policies, procedures, and other controls based on organisational risk priorities'), or potentially MAP-3.5 ('Processes for human oversight are defined, assessed, and documented in accordance with organisational policies from the GOVERN function') — both of which address formalised, documented procedural controls more directly than GOVERN-3.2's role-differentiation framing. A human reviewer should assess whether GOVERN-3.2 is the right subcategory here.

**MANAGE-4.1 (0.75):** The Mapper maps the Article 5 safeguards to post-deployment monitoring, appeal/override, and decommissioning mechanisms, which is a reasonable partial match. However, the obligation's primary concern is *pre-deployment authorisation gating* and *compliance with legal conditions during live use*, not the broader post-deployment lifecycle management that MANAGE-4.1 is designed to address. The phrase 'appeal and override' in MANAGE-4.1 is a partial fit, but the Mapper's reasoning conflates 'scope limitation and authorisation gating' (a legal compliance requirement) with 'post-deployment monitoring plans' (an operational risk management activity). This is a related-but-distinct concern. MANAGE-1.3 ('responses to AI risks deemed high priority are developed, planned, and documented') or GOVERN-1.4 could be stronger fits for the safeguard-operationalisation aspect. The 0.75 score and the hedging in the reasoning ('mapping directly to MANAGE-4.1's post-deployment monitoring and override mechanisms') support flagging this.

**GOVERN-1.1 (0.80):** This mapping is well-reasoned and defensible as an anchor control — the obligation is fundamentally about understanding, managing, and documenting a specific legal compliance requirement. No concerns here.


## EUAIA-OBL-046  ·  Critic confidence 0.82

**Reviewed mappings:** GOVERN-1.1, MANAGE-1.1, MAP-3.3

All three mappings are defensible at a surface level, but two warrant human scrutiny:

1. **MAP-3.3 (0.77)**: The Mapper's reasoning equates 'perimeter and duration of use' with MAP-3.3's 'targeted application scope.' However, MAP-3.3 is primarily concerned with specifying an AI system's *capability-based* application scope during the design/categorisation phase, not with the operational constraints imposed by a legal authorisation regime for each specific deployment event. The obligation's perimeter/duration requirement is more akin to an operational safeguard condition attached to each use authorisation than a system-level scope specification. A stronger candidate in the catalogue would be MAP-1.1 (documenting context-specific laws, deployment settings, and constraints) or potentially MAP-1.6 (system requirements elicited from AI actors accounting for socio-technical implications). The Mapper did not consider these alternatives, suggesting a hedge toward a familiar choice.

2. **MANAGE-1.1 (0.75)**: MANAGE-1.1 addresses the question of whether a system's *overall* deployment should proceed — a go/no-go governance decision at the programme level. The obligation, however, imposes a *per-use* strict-necessity determination tied to a legal authorisation condition (Article 5(2)–(7)), which is closer to an operational compliance check than a programme-level deployment decision. MANAGE-2.4 (mechanisms to deactivate systems performing inconsistently with intended use) or GOVERN-1.1 (already mapped) better reflects the ongoing, per-activation necessity and safeguard checks the Article requires. The reasoning leans on hedging language ('aligning with,' 'which is the deployment-proceed decision') that conflates programme-level go/no-go with per-event legal authorisation.

3. **GOVERN-1.1 (0.80)**: This mapping is the strongest of the three and is defensible. It directly addresses the legal-regulatory documentation duty.

A human reviewer should assess whether MAP-3.3 and MANAGE-1.1 are the most appropriate secondary mappings, and consider whether MAP-1.1 or MAP-1.6 would more precisely capture the perimeter/duration documentation duty, and whether MANAGE-2.4 or GOVERN-1.4/1.5 better covers the per-use necessity and safeguard conditions.


## EUAIA-OBL-047  ·  Critic confidence 0.86

**Reviewed mappings:** GOVERN-1.1, MANAGE-1.1, MAP-5.1

The MAP-5.1 and GOVERN-1.1 mappings are defensible at their respective confidence levels. MAP-5.1 aligns well with the obligation's explicit requirement to assess likelihood, magnitude, and scale of harm and consequences before deployment. GOVERN-1.1 is a sound catch-all for the overarching legal compliance documentation duty.

However, the MANAGE-1.1 mapping at 0.77 warrants flagging. MANAGE-1.1 concerns whether an AI system 'achieves its intended purposes and stated objectives and whether its development or deployment should proceed' — this is primarily a system-level go/no-go decision about ongoing deployment viability, not the per-instance, rights-impact assessment that Article 5(2) mandates. The Mapper's reasoning attempts to reframe a system-level lifecycle decision as a case-by-case deployment authorisation check, which is a category stretch. The reasoning also leans on language ('directly covering the go/no-go deployment determination') that overstates the fit.

A stronger candidate the Mapper did not select is MANAGE-1.3, which covers developing and documenting planned responses to high-priority risks — a closer fit to the obligation's requirement to affirmatively assess and record the seriousness, probability, and scale of harm and rights consequences before each deployment instance. MANAGE-4.1 is also worth a human look, as it addresses post-deployment monitoring, incident response, and override mechanisms that are directly implicated by the rights-and-freedoms consequences assessment in Article 5(2)(b). Neither is proposed as a replacement; the MANAGE-1.1 mapping should be reviewed by a human before the report ships.


## EUAIA-OBL-049  ·  Critic confidence 0.82

**Reviewed mappings:** GOVERN-1.1

GOVERN-1.1 is defensible as a catch-all for legal compliance tracking, but the obligation is substantively more specific than general legal awareness. It mandates two concrete pre-deployment actions: (1) a completed Fundamental Rights Impact Assessment (FRIA) per Article 27, and (2) registration in the EU database per Article 49. These are not merely legal requirements to 'understand and document' — they are structured risk-assessment and accountability artefacts that map more naturally to other subcategories. GOVERN-4.2, which concerns documenting risks and potential impacts of AI systems, aligns closely with the FRIA requirement. MAP-1.1, which requires that context-specific laws, norms, and deployment settings are understood and documented, is a stronger fit for the registration and pre-deployment scoping obligation than GOVERN-1.1 alone. Additionally, MANAGE-4.3, covering incident and error communication and documentation of processes, or MAP-5.1, covering documented likelihood and magnitude of identified impacts, could support the FRIA mapping more directly. The Mapper's reasoning is accurate as far as it goes, but it does not surface whether a more specific control was considered and rejected — the single low-confidence mapping on a highly specific dual-requirement obligation (FRIA + registration) warrants human review to confirm no stronger subcategory was overlooked.


## EUAIA-OBL-050  ·  Critic confidence 0.82

**Reviewed mappings:** GOVERN-1.1, GOVERN-4.2, MAP-5.1

All three mappings are moderate-confidence and collectively defensible in their direction, but MAP-5.1 (0.78) and GOVERN-4.2 (0.75) warrant human scrutiny before the report ships.

**GOVERN-1.1 (0.80):** This is the strongest of the three and is clearly defensible. The FRIA is a specific, documented legal requirement under Article 27 AI Act, and GOVERN-1.1 is the natural anchor for any obligation that primarily concerns understanding, managing, and documenting a regulatory compliance duty. Confirm as solid.

**MAP-5.1 (0.78):** The Mapper's reasoning is substantively attractive — a FRIA is structurally similar to an impact-likelihood-magnitude identification exercise. However, MAP-5.1 is a *system-scoping and risk mapping* control focused on enumerating impacts during the AI lifecycle context-setting phase, not a compliance-process control. The FRIA obligation here is primarily a *legal compliance procedural duty* (complete and evidence a specific Article 27 assessment) imposed on deployers of a narrow category of system, not a general risk-impact enumeration activity. The mapping leans on the structural resemblance between 'impact assessment' and MAP-5.1 rather than a tight conceptual fit. A stronger candidate the Mapper did not select is **GOVERN-4.2** (which was returned as the third mapping) — but more notably, **MANAGE-4.1** (post-deployment monitoring plans including incident response, which touches on deployer-stage obligations) or **MAP-1.1** (understanding context-specific laws, norms, and prospective deployment settings, including legal requirements) could have been considered. The Mapper's reasoning does not hedge excessively, but the fit is driven by analogy to the word 'impact assessment' rather than the control's actual scope.

**GOVERN-4.2 (0.75):** This is the weakest mapping. GOVERN-4.2 is oriented toward *internal team documentation and communication of risks* during design, development, and deployment as an organizational practice — it is a culture and documentation hygiene control. The FRIA under Article 27 is a formal, externally mandated compliance artifact with prescribed content requirements imposed by law on deployers of a specific high-risk system category. While there is surface overlap in 'documenting impacts,' GOVERN-4.2 addresses an organizational practice norm, not a structured regulatory compliance procedure. The reasoning uses the phrase 'directly matching this documentation and communication duty,' which overstates the fit. A human reviewer should assess whether GOVERN-4.2 adds genuine coverage beyond GOVERN-1.1, or whether it is redundant and misleadingly precise.

No single mapping is clearly wrong, but the combination of two sub-0.80 mappings where the reasoning analogizes structure rather than purpose, and the absence of consideration of MAP-1.1 (which explicitly calls out 'context-specific laws, norms and expectations' as part of deployment context documentation), justifies flagging for human review before publication.


## EUAIA-OBL-052  ·  Critic confidence 0.87

**Reviewed mappings:** MAP-3.5, MAP-5.1, MEASURE-2.11

The first two mappings are defensible. MAP-5.1 (0.88) aligns well with the FRIA's duty to assess severity and scale of fundamental rights impacts. MEASURE-2.11 (0.82) is a reasonable fit for the fairness/bias and accuracy documentation requirements of the obligation.

However, MAP-3.5 (0.78) warrants flagging. The obligation's necessity and proportionality analysis — specifically the assessment of whether less intrusive alternatives exist and whether deployment is justified — is a legal proportionality reasoning task, not primarily a human oversight process design task. MAP-3.5 concerns defining and documenting human oversight processes, which is a related-but-distinct concern. The Mapper's reasoning stretches the control by equating 'less intrusive alternatives exist' with 'human oversight processes are defined,' which is not a natural correspondence. The Mapper's reasoning appears to be reaching: necessity/proportionality analysis under the EU AI Act is a substantive legal justification exercise, whereas MAP-3.5 is about human-in-the-loop operational controls.

A stronger candidate the Mapper may have missed is MAP-1.1, which covers understanding and documenting 'context-specific laws, norms and expectations' and 'potential positive and negative impacts,' and includes consideration of the deployment setting — more directly capturing the proportionality and contextual justification duty. Additionally, MEASURE-2.9 (explaining, validating, and documenting the AI model output in context) could have addressed the system performance and accuracy description component more directly than MAP-3.5. Neither is proposed as a replacement; the MAP-3.5 mapping should be reviewed by a human before the report ships.


## EUAIA-OBL-057  ·  Critic confidence 0.87

**Reviewed mappings:** GOVERN-1.7, MANAGE-2.4

Both mappings are partially defensible but warrant human review for the following reasons:

1. MANAGE-2.4 (confidence 0.82): The Mapper's reasoning is reasonable in connecting 'deactivate/disengage' language to immediate cessation of use, but MANAGE-2.4 is specifically scoped to systems performing inconsistently with intended use — not to systems being halted because regulatory authorisation was rejected. The obligation is triggered by a legal/administrative event (rejection of authorisation), not by observed performance failure. This is a related-but-distinct concern from what MANAGE-2.4 addresses. The fit is plausible but not precise.

2. GOVERN-1.7 (confidence 0.78): The Mapper's reasoning uses the framing that an authorisation rejection is 'a specific instance of a decommissioning/phase-out procedure.' However, GOVERN-1.7 addresses planned, process-driven decommissioning to avoid increasing risks — it does not address the acute, legally-mandated immediate deletion of data and outputs that is the core obligation here. The data-deletion and output-discard duty is the most specific and legally significant element of EUAIA-OBL-057, yet it is not addressed by either mapping. A stronger fit for the data-deletion and cessation-upon-legal-trigger elements could be found in MANAGE-4.1 (post-deployment incident response and decommissioning mechanisms) or MANAGE-4.3 (incident response processes followed and documented), neither of which the Mapper considered. The combination of a below-0.80 confidence mapping leaning on hedged framing ('a specific instance of') and the gap in coverage of the data-deletion duty justifies human review before publication.


## EUAIA-OBL-063  ·  Critic confidence 0.87

**Reviewed mappings:** GOVERN-3.2, MANAGE-4.1, MAP-3.5

The GOVERN-3.2 (0.85) and MAP-3.5 (0.80) mappings are defensible: GOVERN-3.2's focus on human-AI configuration roles and oversight responsibilities aligns well with the obligation's requirement for defined competence, training, and authority of the two verifying persons; MAP-3.5's explicit coverage of defining and documenting human oversight processes is a reasonable fit for the dual-verification workflow. However, the MANAGE-4.1 mapping (0.77) is questionable and warrants human review. MANAGE-4.1 addresses broad post-deployment monitoring plans, capturing user input, and appeal/override mechanisms — it is not a natural fit for a highly specific legal requirement that no action may be taken without prior dual-person confirmation. The Mapper's reasoning stretches the 'appeal and override' language to cover what is really a pre-action authorisation gate, which is a distinct concern. The reasoning leans on hedging ('constitutes a mandatory override/confirmation mechanism') to bridge a conceptual gap. A stronger candidate missed by the Mapper is MANAGE-2.4, which specifically addresses mechanisms assigned to 'supersede, disengage, or deactivate AI systems that demonstrate performance or outcomes inconsistent with intended use' and the assignment of responsibilities for overriding AI outputs — more directly capturing the mandatory human gate before acting on RBI identifications. The MANAGE-4.1 mapping should be reviewed before the report ships.

