# TODO: complete remaining MAP/MEASURE/MANAGE subcategories from NIST AI RMF Playbook.
# v1 ships the full GOVERN function (19 subcategories) and a representative 5
# from each of MAP, MEASURE, MANAGE so the mapper has coverage across all four
# functions while we validate end-to-end. Source: NIST AI RMF 1.0 Core, mirrored
# in the AI RMF Playbook (https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook).

from attestloop.schemas import Control

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
            "Processes, procedures, and practices are in place to determine the "
            "needed level of risk management activities based on the "
            "organization's risk tolerance."
        ),
    ),
    Control(
        id="GOVERN-1.4",
        function="GOVERN",
        category="GOVERN-1",
        subcategory_text=(
            "The risk management process and its outcomes are established "
            "through transparent policies, procedures, and other controls based "
            "on organizational risk priorities."
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
            "Roles and responsibilities and lines of communication related to "
            "mapping, measuring, and managing AI risks are documented and are "
            "clear to individuals and teams throughout the organization."
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
            "Executive leadership of the organization takes responsibility for "
            "decisions about risks associated with AI system development and "
            "deployment."
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
            "Policies and procedures are in place to define and differentiate "
            "roles and responsibilities for human-AI configurations and "
            "oversight of AI systems."
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
            "Organizational teams document the risks and potential impacts of "
            "the AI technology they design, develop, deploy, evaluate, and "
            "use, and they communicate about the impacts more broadly."
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
            "consider, prioritize, and integrate feedback from those external "
            "to the team that developed or deployed the AI system regarding "
            "the potential individual and societal impacts related to AI risks."
        ),
    ),
    Control(
        id="GOVERN-5.2",
        function="GOVERN",
        category="GOVERN-5",
        subcategory_text=(
            "Mechanisms are established to enable the team that developed or "
            "deployed AI systems to regularly incorporate adjudicated feedback "
            "from relevant AI actors into system design and implementation."
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
    # ── MAP (representative subset) ───────────────────────────────────────────
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
        id="MAP-2.3",
        function="MAP",
        category="MAP-2",
        subcategory_text=(
            "Scientific integrity and TEVV considerations are identified and "
            "documented, including those related to experimental design, data "
            "collection and selection (e.g., availability, representativeness, "
            "suitability), system trustworthiness, and construct validation."
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
        id="MAP-4.1",
        function="MAP",
        category="MAP-4",
        subcategory_text=(
            "Approaches for mapping AI technology and legal risks of its "
            "components — including the use of third-party data or software — "
            "are in place, followed, and documented, as are risks of "
            "infringement of a third-party's intellectual property or other "
            "rights."
        ),
    ),
    Control(
        id="MAP-5.1",
        function="MAP",
        category="MAP-5",
        subcategory_text=(
            "Likelihood and magnitude of each identified impact (both "
            "potentially beneficial and harmful) based on expected use, past "
            "uses of AI systems in similar contexts, public incident reports, "
            "feedback from those external to the team that developed or "
            "deployed the AI system, or other data are identified and "
            "documented."
        ),
    ),
    # ── MEASURE (representative subset) ───────────────────────────────────────
    Control(
        id="MEASURE-1.1",
        function="MEASURE",
        category="MEASURE-1",
        subcategory_text=(
            "Approaches and metrics for measurement of AI risks enumerated "
            "during the MAP function are selected for implementation starting "
            "with the most significant AI risks. The risks or trustworthiness "
            "characteristics that will not — or cannot — be measured are "
            "properly documented."
        ),
    ),
    Control(
        id="MEASURE-2.1",
        function="MEASURE",
        category="MEASURE-2",
        subcategory_text=(
            "Test sets, metrics, and details about the tools used during TEVV "
            "are documented."
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
        id="MEASURE-4.1",
        function="MEASURE",
        category="MEASURE-4",
        subcategory_text=(
            "Measurement approaches for identifying AI risks are connected to "
            "deployment context(s) and informed through consultation with "
            "domain experts and other end users. Approaches are documented."
        ),
    ),
    # ── MANAGE (representative subset) ────────────────────────────────────────
    Control(
        id="MANAGE-1.1",
        function="MANAGE",
        category="MANAGE-1",
        subcategory_text=(
            "A determination is made as to whether the AI system achieves its "
            "intended purposes and stated objectives and whether its "
            "development or deployment should proceed."
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
        id="MANAGE-2.2",
        function="MANAGE",
        category="MANAGE-2",
        subcategory_text=(
            "Mechanisms are in place and applied to sustain the value of "
            "deployed AI systems."
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
]
