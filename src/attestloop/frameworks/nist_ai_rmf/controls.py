from attestloop.schemas import Control

# Source: NIST AI Risk Management Framework 1.0 Core, mirrored in the
# AI RMF Playbook (https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook).
# Subcategory text follows the published Core. Function and category labels
# use the dash-cased form ("GOVERN-1") consistent with the rest of the codebase.

CONTROLS: list[Control] = [
    # ── GOVERN ────────────────────────────────────────────────────────────────
    Control(
        id="GOVERN-1.1",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "Legal and regulatory requirements involving AI are understood, "
            "managed, and documented."
        ),
    ),
    Control(
        id="GOVERN-1.2",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "The characteristics of trustworthy AI are integrated into "
            "organizational policies, processes, procedures, and practices."
        ),
    ),
    Control(
        id="GOVERN-1.3",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "Processes, procedures, and practices are in place to determine "
            "the needed level of risk management activities based on the "
            "organization's risk tolerance."
        ),
    ),
    Control(
        id="GOVERN-1.4",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "The risk management process and its outcomes are established "
            "through transparent policies, procedures, and other controls "
            "based on organizational risk priorities."
        ),
    ),
    Control(
        id="GOVERN-1.5",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "Ongoing monitoring and periodic review of the risk management "
            "process and its outcomes are planned, with organizational roles "
            "and responsibilities clearly defined, including determining the "
            "frequency of periodic review."
        ),
    ),
    Control(
        id="GOVERN-1.6",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "Mechanisms are in place to inventory AI systems and are "
            "resourced according to organizational risk priorities."
        ),
    ),
    Control(
        id="GOVERN-1.7",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "Processes and procedures are in place for decommissioning and "
            "phasing out of AI systems safely and in a manner that does not "
            "increase risks or decrease the organization's trustworthiness."
        ),
    ),
    Control(
        id="GOVERN-2.1",
        function="GOVERN",
        category="GOVERN-2",
        subcategory_text=(
            "Roles and responsibilities and lines of communication related "
            "to mapping, measuring, and managing AI risks are documented and "
            "are clear to individuals and teams throughout the organization."
        ),
    ),
    Control(
        id="GOVERN-2.2",
        function="GOVERN",
        category="GOVERN-2",
        subcategory_text=(
            "The organization's personnel and partners receive AI risk "
            "management training to enable them to perform their duties and "
            "responsibilities consistent with related policies, procedures, "
            "and agreements."
        ),
    ),
    Control(
        id="GOVERN-2.3",
        function="GOVERN",
        category="GOVERN-2",
        subcategory_text=(
            "Executive leadership of the organization takes responsibility "
            "for decisions about risks associated with AI system development "
            "and deployment."
        ),
    ),
    Control(
        id="GOVERN-3.1",
        function="GOVERN",
        category="GOVERN-3",
        subcategory_text=(
            "Decision-making related to mapping, measuring, and managing AI "
            "risks throughout the lifecycle is informed by a diverse team "
            "(e.g., diversity of demographics, disciplines, experience, "
            "expertise, and backgrounds)."
        ),
    ),
    Control(
        id="GOVERN-3.2",
        function="GOVERN",
        category="GOVERN-3",
        subcategory_text=(
            "Policies and procedures are in place to define and "
            "differentiate roles and responsibilities for human-AI "
            "configurations and oversight of AI systems."
        ),
    ),
    Control(
        id="GOVERN-4.1",
        function="GOVERN",
        category="GOVERN-4",
        subcategory_text=(
            "Organizational policies and practices are in place to foster a "
            "critical thinking and safety-first mindset in the design, "
            "development, deployment, and uses of AI systems to minimize "
            "potential negative impacts."
        ),
    ),
    Control(
        id="GOVERN-4.2",
        function="GOVERN",
        category="GOVERN-4",
        subcategory_text=(
            "Organizational teams document the risks and potential impacts "
            "of the AI technology they design, develop, deploy, evaluate, "
            "and use, and they communicate about the impacts more broadly."
        ),
    ),
    Control(
        id="GOVERN-4.3",
        function="GOVERN",
        category="GOVERN-4",
        subcategory_text=(
            "Organizational practices are in place to enable AI testing, "
            "identification of incidents, and information sharing."
        ),
    ),
    Control(
        id="GOVERN-5.1",
        function="GOVERN",
        category="GOVERN-5",
        subcategory_text=(
            "Organizational policies and practices are in place to collect, "
            "consider, prioritize, and integrate feedback from those "
            "external to the team that developed or deployed the AI system "
            "regarding the potential individual and societal impacts related "
            "to AI risks."
        ),
    ),
    Control(
        id="GOVERN-5.2",
        function="GOVERN",
        category="GOVERN-5",
        subcategory_text=(
            "Mechanisms are established to enable the team that developed "
            "or deployed AI systems to regularly incorporate adjudicated "
            "feedback from relevant AI actors into system design and "
            "implementation."
        ),
    ),
    Control(
        id="GOVERN-6.1",
        function="GOVERN",
        category="GOVERN-6",
        subcategory_text=(
            "Policies and procedures are in place that address AI risks "
            "associated with third-party entities, including risks of "
            "infringement of a third party's intellectual property or other "
            "rights."
        ),
    ),
    Control(
        id="GOVERN-6.2",
        function="GOVERN",
        category="GOVERN-6",
        subcategory_text=(
            "Contingency processes are in place to handle failures or "
            "incidents in third-party data or AI systems deemed to be "
            "high-risk."
        ),
    ),
    # ── MAP ───────────────────────────────────────────────────────────────────
    Control(
        id="MAP-1.1",
        function="MAP",
        category="MAP-1",
        subcategory_text=(
            "Intended purposes, potentially beneficial uses, context-specific "
            "laws, norms and expectations, and prospective settings in which "
            "the AI system will be deployed are understood and documented. "
            "Considerations include the specific set or types of users along "
            "with their expectations; potential positive and negative impacts "
            "of system uses to individuals, communities, organizations, "
            "society, and the planet; assumptions and related limitations "
            "about AI system purpose, uses, and risks across the development "
            "or product AI lifecycle; and related TEVV and system metrics."
        ),
    ),
    Control(
        id="MAP-1.2",
        function="MAP",
        category="MAP-1",
        subcategory_text=(
            "Inter-disciplinary AI actors, competencies, skills, and "
            "capacities for establishing context reflect demographic "
            "diversity and broad domain and user experience expertise, and "
            "their participation is documented. Opportunities for "
            "interdisciplinary collaboration are prioritized."
        ),
    ),
    Control(
        id="MAP-1.3",
        function="MAP",
        category="MAP-1",
        subcategory_text=(
            "The organization's mission and relevant goals for AI technology "
            "are understood and documented."
        ),
    ),
    Control(
        id="MAP-1.4",
        function="MAP",
        category="MAP-1",
        subcategory_text=(
            "The business value or context of business use has been clearly "
            "defined or — in the case of assessing existing AI systems — "
            "re-evaluated."
        ),
    ),
    Control(
        id="MAP-1.5",
        function="MAP",
        category="MAP-1",
        subcategory_text=(
            "Organizational risk tolerances are determined and documented."
        ),
    ),
    Control(
        id="MAP-1.6",
        function="MAP",
        category="MAP-1",
        subcategory_text=(
            "System requirements (e.g., \"the system shall respect the "
            "privacy of its users\") are elicited from and understood by "
            "relevant AI actors. Design decisions take socio-technical "
            "implications into account to address AI risks."
        ),
    ),
    Control(
        id="MAP-2.1",
        function="MAP",
        category="MAP-2",
        subcategory_text=(
            "The specific tasks and methods used to implement the tasks "
            "that the AI system will support are defined (e.g., classifiers, "
            "generative models, recommenders)."
        ),
    ),
    Control(
        id="MAP-2.2",
        function="MAP",
        category="MAP-2",
        subcategory_text=(
            "Information about the AI system's knowledge limits and how "
            "system output may be utilized and overseen by humans is "
            "documented. Documentation provides sufficient information to "
            "assist relevant AI actors when making decisions and taking "
            "subsequent actions."
        ),
    ),
    Control(
        id="MAP-2.3",
        function="MAP",
        category="MAP-2",
        subcategory_text=(
            "Scientific integrity and TEVV considerations are identified "
            "and documented, including those related to experimental design, "
            "data collection and selection (e.g., availability, "
            "representativeness, suitability), system trustworthiness, and "
            "construct validation."
        ),
    ),
    Control(
        id="MAP-3.1",
        function="MAP",
        category="MAP-3",
        subcategory_text=(
            "Potential benefits of intended AI system functionality and "
            "performance are examined and documented."
        ),
    ),
    Control(
        id="MAP-3.2",
        function="MAP",
        category="MAP-3",
        subcategory_text=(
            "Potential costs, including non-monetary costs, which result "
            "from expected or realized AI errors or system functionality "
            "and trustworthiness — as connected to organizational risk "
            "tolerance — are examined and documented."
        ),
    ),
    Control(
        id="MAP-3.3",
        function="MAP",
        category="MAP-3",
        subcategory_text=(
            "Targeted application scope is specified and documented based "
            "on the system's capability, established context, and AI system "
            "categorization."
        ),
    ),
    Control(
        id="MAP-3.4",
        function="MAP",
        category="MAP-3",
        subcategory_text=(
            "Processes for operator and practitioner proficiency with AI "
            "system performance and trustworthiness — and relevant technical "
            "standards and certifications — are defined, assessed, and "
            "documented."
        ),
    ),
    Control(
        id="MAP-3.5",
        function="MAP",
        category="MAP-3",
        subcategory_text=(
            "Processes for human oversight are defined, assessed, and "
            "documented in accordance with organizational policies from the "
            "GOVERN function."
        ),
    ),
    Control(
        id="MAP-4.1",
        function="MAP",
        category="MAP-4",
        subcategory_text=(
            "Approaches for mapping AI technology and legal risks of its "
            "components — including the use of third-party data or "
            "software — are in place, followed, and documented, as are "
            "risks of infringement of a third-party's intellectual property "
            "or other rights."
        ),
    ),
    Control(
        id="MAP-4.2",
        function="MAP",
        category="MAP-4",
        subcategory_text=(
            "Internal risk controls for components of the AI system, "
            "including third-party AI technologies, are identified and "
            "documented."
        ),
    ),
    Control(
        id="MAP-5.1",
        function="MAP",
        category="MAP-5",
        subcategory_text=(
            "Likelihood and magnitude of each identified impact (both "
            "potentially beneficial and harmful) based on expected use, "
            "past uses of AI systems in similar contexts, public incident "
            "reports, feedback from those external to the team that "
            "developed or deployed the AI system, or other data are "
            "identified and documented."
        ),
    ),
    Control(
        id="MAP-5.2",
        function="MAP",
        category="MAP-5",
        subcategory_text=(
            "Practices and personnel for supporting regular engagement with "
            "relevant AI actors and integrating feedback about positive, "
            "negative, and unanticipated impacts are in place and "
            "documented."
        ),
    ),
    # ── MEASURE ───────────────────────────────────────────────────────────────
    Control(
        id="MEASURE-1.1",
        function="MEASURE",
        category="MEASURE-1",
        subcategory_text=(
            "Approaches and metrics for measurement of AI risks enumerated "
            "during the MAP function are selected for implementation "
            "starting with the most significant AI risks. The risks or "
            "trustworthiness characteristics that will not — or cannot — be "
            "measured are properly documented."
        ),
    ),
    Control(
        id="MEASURE-1.2",
        function="MEASURE",
        category="MEASURE-1",
        subcategory_text=(
            "Appropriateness of AI metrics and effectiveness of existing "
            "controls are regularly assessed and updated, including reports "
            "of errors and potential impacts on affected communities."
        ),
    ),
    Control(
        id="MEASURE-1.3",
        function="MEASURE",
        category="MEASURE-1",
        subcategory_text=(
            "Internal experts who did not serve as front-line developers "
            "for the system and/or independent assessors are involved in "
            "regular assessments and updates. Domain experts, users, AI "
            "actors external to the team that developed or deployed the AI "
            "system, and affected communities are consulted in support of "
            "assessments as necessary per organizational risk tolerance."
        ),
    ),
    Control(
        id="MEASURE-2.1",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Test sets, metrics, and details about the tools used during "
            "TEVV are documented."
        ),
    ),
    Control(
        id="MEASURE-2.2",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Evaluations involving human subjects meet applicable "
            "requirements (including human subject protection) and are "
            "representative of the relevant population."
        ),
    ),
    Control(
        id="MEASURE-2.3",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "AI system performance or assurance criteria are measured "
            "qualitatively or quantitatively and demonstrated for "
            "conditions similar to deployment setting(s). Measures are "
            "documented."
        ),
    ),
    Control(
        id="MEASURE-2.4",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "The functionality and behavior of the AI system and its "
            "components — as identified in the MAP function — are monitored "
            "when in production."
        ),
    ),
    Control(
        id="MEASURE-2.5",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "The AI system to be deployed is demonstrated to be valid and "
            "reliable. Limitations of the generalizability beyond the "
            "conditions under which the technology was developed are "
            "documented."
        ),
    ),
    Control(
        id="MEASURE-2.6",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "The AI system is evaluated regularly for safety risks — as "
            "identified in the MAP function. The AI system to be deployed "
            "is demonstrated to be safe, its residual negative risk does "
            "not exceed the risk tolerance, and it can fail safely, "
            "particularly if made to operate beyond its knowledge limits. "
            "Safety metrics reflect system reliability and robustness, "
            "real-time monitoring, and response times for AI system "
            "failures."
        ),
    ),
    Control(
        id="MEASURE-2.7",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "AI system security and resilience — as identified in the MAP "
            "function — are evaluated and documented."
        ),
    ),
    Control(
        id="MEASURE-2.8",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Risks associated with transparency and accountability — as "
            "identified in the MAP function — are examined and documented."
        ),
    ),
    Control(
        id="MEASURE-2.9",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "The AI model is explained, validated, and documented, and AI "
            "system output is interpreted within its context — as "
            "identified in the MAP function — to inform responsible use "
            "and governance."
        ),
    ),
    Control(
        id="MEASURE-2.10",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Privacy risk of the AI system — as identified in the MAP "
            "function — is examined and documented."
        ),
    ),
    Control(
        id="MEASURE-2.11",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Fairness and bias — as identified in the MAP function — are "
            "evaluated and results are documented."
        ),
    ),
    Control(
        id="MEASURE-2.12",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Environmental impact and sustainability of AI model training "
            "and management activities — as identified in the MAP "
            "function — are assessed and documented."
        ),
    ),
    Control(
        id="MEASURE-2.13",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Effectiveness of the employed TEVV metrics and processes in "
            "the MEASURE function are evaluated and documented."
        ),
    ),
    Control(
        id="MEASURE-3.1",
        function="MEASURE",
        category="MEASURE-3",
        subcategory_text=(
            "Approaches, personnel, and documentation are in place to "
            "regularly identify and track existing, unanticipated, and "
            "emergent AI risks based on factors such as intended and actual "
            "performance in deployed contexts."
        ),
    ),
    Control(
        id="MEASURE-3.2",
        function="MEASURE",
        category="MEASURE-3",
        subcategory_text=(
            "Risk tracking approaches are considered for settings where AI "
            "risks are difficult to assess using currently available "
            "measurement techniques or where metrics are not yet available."
        ),
    ),
    Control(
        id="MEASURE-3.3",
        function="MEASURE",
        category="MEASURE-3",
        subcategory_text=(
            "Feedback processes for end users and impacted communities to "
            "report problems and appeal system outcomes are established and "
            "integrated into AI system evaluation metrics."
        ),
    ),
    Control(
        id="MEASURE-4.1",
        function="MEASURE",
        category="MEASURE-4",
        subcategory_text=(
            "Measurement approaches for identifying AI risks are connected "
            "to deployment context(s) and informed through consultation "
            "with domain experts and other end users. Approaches are "
            "documented."
        ),
    ),
    Control(
        id="MEASURE-4.2",
        function="MEASURE",
        category="MEASURE-4",
        subcategory_text=(
            "Measurement results regarding AI system trustworthiness in "
            "deployment context(s) and across the AI lifecycle are "
            "informed by input from domain experts and relevant AI actors "
            "to validate whether the system is performing consistently as "
            "intended. Results are documented."
        ),
    ),
    Control(
        id="MEASURE-4.3",
        function="MEASURE",
        category="MEASURE-4",
        subcategory_text=(
            "Measurable performance improvements or declines based on "
            "consultations with relevant AI actors, including affected "
            "communities, and field data about context-relevant risks and "
            "trustworthiness characteristics are identified and documented."
        ),
    ),
    # ── MANAGE ────────────────────────────────────────────────────────────────
    Control(
        id="MANAGE-1.1",
        function="MANAGE",
        category="MANAGE-1",
        subcategory_text=(
            "A determination is made as to whether the AI system achieves "
            "its intended purposes and stated objectives and whether its "
            "development or deployment should proceed."
        ),
    ),
    Control(
        id="MANAGE-1.2",
        function="MANAGE",
        category="MANAGE-1",
        subcategory_text=(
            "Treatment of documented AI risks is prioritized based on "
            "impact, likelihood, and available resources or methods."
        ),
    ),
    Control(
        id="MANAGE-1.3",
        function="MANAGE",
        category="MANAGE-1",
        subcategory_text=(
            "Responses to the AI risks deemed high priority — as identified "
            "by the MAP function — are developed, planned, and documented. "
            "Risk response options can include mitigating, transferring, "
            "avoiding, or accepting."
        ),
    ),
    Control(
        id="MANAGE-1.4",
        function="MANAGE",
        category="MANAGE-1",
        subcategory_text=(
            "Negative residual risks (defined as the sum of all unmitigated "
            "risks) to both downstream acquirers of AI systems and end "
            "users are documented."
        ),
    ),
    Control(
        id="MANAGE-2.1",
        function="MANAGE",
        category="MANAGE-2",
        subcategory_text=(
            "Resources required to manage AI risks are taken into account — "
            "along with viable non-AI alternative systems, approaches, or "
            "methods — to reduce the magnitude or likelihood of potential "
            "impacts."
        ),
    ),
    Control(
        id="MANAGE-2.2",
        function="MANAGE",
        category="MANAGE-2",
        subcategory_text=(
            "Mechanisms are in place and applied to sustain the value of "
            "deployed AI systems."
        ),
    ),
    Control(
        id="MANAGE-2.3",
        function="MANAGE",
        category="MANAGE-2",
        subcategory_text=(
            "Procedures are followed to respond to and recover from a "
            "previously unknown risk when it is identified."
        ),
    ),
    Control(
        id="MANAGE-2.4",
        function="MANAGE",
        category="MANAGE-2",
        subcategory_text=(
            "Mechanisms are in place and applied, and responsibilities are "
            "assigned and understood, to supersede, disengage, or "
            "deactivate AI systems that demonstrate performance or outcomes "
            "inconsistent with intended use."
        ),
    ),
    Control(
        id="MANAGE-3.1",
        function="MANAGE",
        category="MANAGE-3",
        subcategory_text=(
            "AI risks and benefits from third-party resources are regularly "
            "monitored, and risk controls are applied and documented."
        ),
    ),
    Control(
        id="MANAGE-3.2",
        function="MANAGE",
        category="MANAGE-3",
        subcategory_text=(
            "Pre-trained models which are used for development are "
            "monitored as part of AI system regular monitoring and "
            "maintenance."
        ),
    ),
    Control(
        id="MANAGE-4.1",
        function="MANAGE",
        category="MANAGE-4",
        subcategory_text=(
            "Post-deployment AI system monitoring plans are implemented, "
            "including mechanisms for capturing and evaluating input from "
            "users and other relevant AI actors, appeal and override, "
            "decommissioning, incident response, recovery, and change "
            "management."
        ),
    ),
    Control(
        id="MANAGE-4.2",
        function="MANAGE",
        category="MANAGE-4",
        subcategory_text=(
            "Measurable activities for continual improvements are "
            "integrated into AI system updates and include regular "
            "engagement with interested parties, including relevant AI "
            "actors."
        ),
    ),
    Control(
        id="MANAGE-4.3",
        function="MANAGE",
        category="MANAGE-4",
        subcategory_text=(
            "Incidents and errors are communicated to relevant AI actors, "
            "including affected communities. Processes for tracking, "
            "responding to, and recovering from incidents and errors are "
            "followed and documented."
        ),
    ),
]
