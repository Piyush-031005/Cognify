from database import get_conn
from datetime import datetime
import random
from semantic_engine import (
    generate_semantic_id,
    generate_variant_id
)

# ==========================================
# MASTER MAP (EXPANDED TO 16 SUBJECTS & TOPICS)
# ==========================================

MASTER_MAP = {
    # 1. DSA
    ("dsa", "arrays", "basics"): [
        "array indexing",
        "contiguous memory layout",
        "insertion complexity",
        "searching algorithms",
        "array deletion"
    ],
    ("dsa", "linked_lists", "singly_linked"): [
        "node reference pointer",
        "head insertion",
        "tail traversal",
        "pointer manipulation",
        "memory overhead"
    ],
    ("dsa", "graphs", "traversals"): [
        "breadth first search",
        "depth first search",
        "visited node set",
        "adjacency list",
        "shortest path routing"
    ],

    # 2. MATH
    ("math", "algebra", "quadratic"): [
        "discriminant",
        "roots of quadratic",
        "nature of roots",
        "quadratic formula",
        "graph behavior"
    ],
    ("math", "calculus", "derivatives"): [
        "rate of change",
        "tangent line slope",
        "chain rule derivative",
        "critical points limit",
        "inflection optimization"
    ],
    ("math", "probability", "distributions"): [
        "normal distribution bell",
        "binomial success probability",
        "mean variance deviation",
        "independent events joint",
        "conditional probability theorem"
    ],

    # 3. PHYSICS
    ("physics", "classical_mechanics", "laws_of_motion"): [
        "inertia and mass",
        "rotational mass",
        "rotational inertia calculation",
        "angular momentum"
    ],
    ("physics", "thermodynamics", "heat_transfer"): [
        "thermal conduction flow",
        "convection current density",
        "radiation wavelength emission",
        "entropy thermodynamic disorder",
        "first law energy"
    ],
    ("physics", "electromagnetism", "circuits"): [
        "ohm law resistance",
        "kirchhoff current loop",
        "capacitance charge storage",
        "magnetic flux induction",
        "power dissipation heat"
    ],

    # 4. CHEMISTRY
    ("chemistry", "organic_chemistry", "functional_groups"): [
        "isomerism",
        "stereoisomerism",
        "chiral centers",
        "stereocenters"
    ],
    ("chemistry", "physical_chemistry", "rates"): [
        "activation energy barrier",
        "catalyst rate acceleration",
        "half life decay",
        "reaction order concentration",
        "equilibrium constant ratio"
    ],
    ("chemistry", "inorganic_chemistry", "bonding"): [
        "covalent sharing bonds",
        "ionic electrostatic attraction",
        "electronegativity atom pull",
        "hybridization orbital shape",
        "metallic sea electrons"
    ],

    # 5. BIOLOGY
    ("biology", "genetics", "mendelian_inheritance"): [
        "mendelian laws",
        "punnett squares",
        "dihybrid crosses",
        "genotypic ratios"
    ],
    ("biology", "cell_biology", "organelles"): [
        "mitochondrion ATP respiration",
        "nucleus gene replication",
        "ribosome protein translation",
        "lysosome waste digestion",
        "membrane selective permeability"
    ],
    ("biology", "ecology", "ecosystems"): [
        "trophic level energy",
        "food web interaction",
        "carrying capacity limit",
        "nitrogen fixation bacteria",
        "biodiversity species resilience"
    ],

    # 6. ENGLISH
    ("english", "grammar", "sentence_structure"): [
        "modifiers placement",
        "dangling modifiers",
        "subject implied",
        "corrections"
    ],
    ("english", "vocabulary", "context_clues"): [
        "synonym inference clues",
        "antonym contrast signals",
        "metaphorical language intent",
        "etymology root origins",
        "homophone spelling distinctions"
    ],

    # 7. HISTORY
    ("history", "world_history", "ancient_civilizations"): [
        "mesopotamian code Hammurabi",
        "egyptian hierarchy pharaoh",
        "roman republic senate",
        "silk road trade",
        "greek democracy assembly"
    ],
    ("history", "modern_history", "industrial_revolution"): [
        "steam engine mechanization",
        "urbanization labor shifts",
        "capitalism free market",
        "factory system division",
        "transportation rail network"
    ],

    # 8. GEOGRAPHY
    ("geography", "physical_geography", "plate_tectonics"): [
        "continental drift theory",
        "subduction zone trenches",
        "convergent boundary fold",
        "divergent boundary ridge",
        "seismic wave propagation"
    ],
    ("geography", "human_geography", "demographics"): [
        "population density distribution",
        "migration push pull",
        "urban sprawl expansion",
        "fertility rate decline",
        "demographic transition model"
    ],

    # 9. ECONOMICS
    ("economics", "microeconomics", "supply_demand"): [
        "market equilibrium price",
        "elasticity of demand",
        "consumer surplus utility",
        "marginal utility cost",
        "opportunity cost trade"
    ],
    ("economics", "macroeconomics", "monetary_policy"): [
        "inflation index purchasing",
        "interest rate control",
        "gdp output calculation",
        "unemployment rate metric",
        "central bank reserve"
    ],

    # 10. PROGRAMMING
    ("programming", "python", "core_concepts"): [
        "list comprehension syntax",
        "generator yield memory",
        "decorator function wrapping",
        "dynamically typed variable",
        "gil concurrency constraint"
    ],
    ("programming", "java", "oop"): [
        "polymorphism runtime method",
        "inheritance class hierarchy",
        "encapsulation private fields",
        "abstraction interface contracts",
        "garbage collection sweep"
    ],
    ("programming", "cpp", "pointers"): [
        "raw pointers memory",
        "smart pointers unique",
        "reference variable alias",
        "destructor memory release",
        "virtual table dispatch"
    ],

    # 11. DBMS
    ("dbms", "sql", "joins"): [
        "inner join intersect",
        "left outer join",
        "cross join product",
        "group by aggregate",
        "subquery execution order"
    ],
    ("dbms", "normalization", "normal_forms"): [
        "first normal form",
        "second normal form",
        "third normal form",
        "boyce codd form",
        "functional dependency key"
    ],

    # 12. OS
    ("os", "processes", "scheduling"): [
        "context switching overhead",
        "cpu scheduler dispatch",
        "round robin time slice",
        "deadlock prevention conditions",
        "semaphore thread sync"
    ],
    ("os", "memory_management", "paging"): [
        "virtual memory mapping",
        "page fault swap",
        "tlb translation cache",
        "fragmentation internal external",
        "lru page replacement"
    ],

    # 13. CN
    ("cn", "protocols", "tcp_ip"): [
        "three way handshake",
        "sliding window control",
        "ip routing subnet",
        "dns name resolution",
        "dhcp address lease"
    ],

    # 14. ML
    ("ml", "supervised_learning", "classification"): [
        "gradient descent steps",
        "overfitting model bias",
        "regularization l1 l2",
        "precision recall f1",
        "decision tree splits"
    ],

    # 15. AI
    ("ai", "search_algorithms", "heuristics"): [
        "minimax adversarial search",
        "alpha beta pruning",
        "a star distance",
        "heuristic evaluation cost",
        "genetic algorithm crossover"
    ],

    # 16. APTITUDE
    ("aptitude", "quantitative", "arithmetic"): [
        "compound interest growth",
        "ratio proportion scales",
        "speed distance relative",
        "permutation arrangement count",
        "probability outcomes sample"
    ]
}

# ==========================================
# OPTION BANK
# ==========================================

OPTION_BANK = {
    # DSA
    "array indexing": ["Direct index offsets", "Sequential memory scan", "Pointer search", "Hash indexing"],
    "contiguous memory layout": ["Contiguous block allocation", "Linked pointers list", "Indexed segmented nodes", "Stack memory frames"],
    "insertion complexity": ["O(n) linear shift time", "O(1) constant time", "O(log n) logarithmic time", "O(n log n)"],
    "searching algorithms": ["Binary search on sorted lists", "Linear scan on unsorted lists", "Depth-first traversal", "Breadth-first expansion"],
    "array deletion": ["Requires elements shifting", "Immediate memory release", "Pointer relocation", "Null index fill"],
    "node reference pointer": ["Memory link address references", "Node key value indices", "Double pointer addresses", "Reference keys"],
    "head insertion": ["O(1) pointer updates only", "O(n) elements shifting", "O(log n) tree balance", "Constant array shift"],
    "tail traversal": ["O(n) sequence scanning", "O(1) direct reference pointer", "O(log n) root traverse", "Index pointer direct"],
    "pointer manipulation": ["Updating next link references", "Reallocating array memory blocks", "Adjusting elements capacity indices", "Shifting array keys"],
    "memory overhead": ["Individual node address reference fields", "Sequential indexes allocation lists", "Static array blocks size", "Hash slot allocations"],
    "breadth first search": ["Queue-based level traversal", "Stack-based depth exploration", "Recursive root nodes evaluation", "Direct hash index lookup"],
    "depth first search": ["Stack-based branch traversal", "Queue-based level scanning", "Hash table index tracking", "Heap queue priority sorting"],
    "visited node set": ["Prevents infinite cycle traps", "Stores target node keys", "Calculates path traversal distance", "Maintains branch priority queue"],
    "adjacency list": ["Linked representation of connections", "Contiguous index matrix table", "Hash index slot array", "Flat binary list file"],
    "shortest path routing": ["Dijkstra distance relaxation check", "Binary depth path analysis", "BFS leaf nodes verification", "In-order path scanning"],

    # MATH
    "discriminant": ["b²-4ac expression", "a²-4bc expression", "b²+4ac expression", "a²+b²-c²"],
    "roots of quadratic": ["Solutions making function zero", "Extreme vertex coordinates", "Derivatives values", "Function integration bounds"],
    "nature of roots": ["Real or imaginary domain", "Positive or negative signs", "Ascending or descending direction", "Stable or unstable behavior"],
    "quadratic formula": ["(-b±√D)/2a solutions", "(b±√D)/2a solutions", "(-b±D)/2a solutions", "(b±D)/2a solutions"],
    "graph behavior": ["Parabolic symmetry shape", "Linear direction path", "Circular radius loop", "Hyperbolic curve segments"],
    "rate of change": ["Instantaneous function derivative value", "Accumulated sum integration area", "Secant slope average change", "Static value coordinates"],
    "tangent line slope": ["Limit of secant slopes", "Integral under curves boundaries", "Y-intercept value coordinates", "Radius circle bounds"],
    "chain rule derivative": ["Composition function differentiation rule", "Product function differentiation rule", "Quotient function differentiation rule", "Power rule expansion"],
    "critical points limit": ["Derivative value equals zero", "Function cross origin point", "Inflection concavity inflection point", "Secant line intersection"],
    "inflection optimization": ["Concavity shift boundary coordinates", "Maximum local derivative peaks", "Tangent line crossing axes", "Zero function limits"],
    "normal distribution bell": ["Symmetric mean centered curve", "Exponential growth decline curve", "Slashed uniform flat distribution", "Discrete step function curve"],
    "binomial success probability": ["Fixed trials binary outcomes", "Infinite trials continuous variables", "Exponential arrival frequency rate", "Normal bell curves bounds"],
    "mean variance deviation": ["Central tendency spread variables", "Cumulative bounds area value", "Independent variables joint value", "Derivative slope lines"],
    "independent events joint": ["Product of individual probabilities", "Sum of individual probabilities", "Conditional probability division value", "Zero state probability"],
    "conditional probability theorem": ["Bayes ratio probability updates", "Joint product intersection values", "Uniform distribution bounds area", "Secant lines slopes"],

    # PHYSICS
    "inertia and mass": ["Resistance to motion changes", "Force of gravity pull", "Velocity change rate", "Work energy ratio"],
    "rotational mass": ["Moment of inertia resistance", "Angular velocity speed", "Linear state state weight", "Centripetal force pull"],
    "rotational inertia calculation": ["Integral mass distribution sum", "Pure total mass sum", "Angular momentum ratio", "Linear weight acceleration"],
    "angular momentum": ["Momentum in rotational system", "Linear velocity momentum", "Torque balance force", "Centripetal state pull"],
    "thermal conduction flow": ["Direct kinetic contact transfer", "Fluid mass density cycles", "Electromagnetic wave emissions", "Entropy decay changes"],
    "convection current density": ["Fluid mass density differences", "Direct solid molecular contact", "Photon transfer wavelengths", "Absolute vacuum flow"],
    "radiation wavelength emission": ["Electromagnetic photon waves propagation", "Kinetic contact molecule transfers", "Fluid current movement loops", "Conduction flow rate"],
    "entropy thermodynamic disorder": ["Irreversible system state disorder", "Total internal energy conservation", "Heat capacity temperature ratio", "Kinetic energy speed"],
    "first law energy": ["Energy conservation heat work", "Entropy increases naturally systems", "Absolute zero state limits", "Velocity acceleration gravity"],
    "ohm law resistance": ["Current voltage resistance ratio", "Electromagnetic flux loop values", "Capacitor charge capacity limits", "Power heat loss lines"],
    "kirchhoff current loop": ["Conservation of charge loops", "Magnetic induction flux paths", "Thermal dissipation rate lines", "Ohm law ratios"],
    "capacitance charge storage": ["Electric field charge storage", "Magnetic flux induction paths", "Dissipated thermal energy fields", "Voltage current balance"],
    "magnetic flux induction": ["Faraday electromotive force changes", "Kirchhoff current loop balances", "Ohmic resistance thermal dissipation", "Capacitive charge state"],
    "power dissipation heat": ["I²R thermal loss rate", "Voltage potential charge loops", "Capacitive field storage values", "Magnetic flux lines"],

    # CHEMISTRY
    "isomerism": ["Same formula unique structure", "Unique formula same structure", "Identical spatial shapes", "Mirror spatial shapes"],
    "stereoisomerism": ["Spatial dimensional arrangement configurations", "Functional group structural variations", "Atom alignment bonds", "Stereocenter splits"],
    "chiral centers": ["Four distinct bonded groups carbons", "Three bonded groups carbons", "Double bonded carbons", "Symmetric side groups"],
    "stereocenters": ["Asymmetric carbon configuration centers", "Functional group core centers", "Double bond cores", "Aromatic rings"],
    "activation energy barrier": ["Minimum reaction energy threshold", "Catalyst speed increase limit", "Reaction equilibrium ratio constant", "Half life duration bounds"],
    "catalyst rate acceleration": ["Lowering activation energy barrier", "Increasing reaction temperature limits", "Shifting equilibrium constant value", "Prolonging half life duration"],
    "half life decay": ["Time for half concentration", "Total reaction complete duration", "Catalyst acceleration trigger rate", "Equilibrium ratio limit"],
    "reaction order concentration": ["Concentration dependency exponent factor", "Total molecule mass weight", "Catalyst state surface area", "Activation energy balance"],
    "equilibrium constant ratio": ["Product reactant ratio constant", "Activation energy threshold balance", "Reaction speed rate constant", "Half concentration time"],
    "covalent sharing bonds": ["Electron pair sharing bonds", "Electrostatic attraction bond pairs", "Electron sea sharing fields", "Orbital hybrid splits"],
    "ionic electrostatic attraction": ["Opposite charges electrostatic forces", "Shared electron pair bonds", "Electronegativity pull differentials", "Delocalized electron sea"],
    "electronegativity atom pull": ["Shared electrons attraction pull", "Ionic charges electrostatic forces", "Orbital hybrid configuration splits", "Delocalized electron sea"],
    "hybridization orbital shape": ["Atomic orbital mixing configurations", "Opposite charge electrostatic forces", "Ionic bond sharing pairs", "Delocalized electron fields"],
    "metallic sea electrons": ["Delocalized valence electron clouds", "Atomic orbital hybrid mix", "Opposite charges electrostatic pull", "Shared electron pair bonds"],

    # BIOLOGY
    "mendelian laws": ["Segregation and independent assortment laws", "Linked genes chromosome crossing", "Natural traits selection", "Phenotypic dilution ratios"],
    "punnett squares": ["Genotypic crossing prediction grids", "Pedigree history logs", "Chromosome division charts", "Linked traits list"],
    "dihybrid crosses": ["Double traits inheritance checking", "Single trait inheritance checking", "Sex-linked trait analysis", "Gene mutation tracking"],
    "genotypic ratios": ["Offspring genetic traits ratios", "Visual trait percentage", "Survival fitness rate", "Mutation frequency"],
    "mitochondrion ATP respiration": ["Cellular ATP respiration center", "Genetic DNA replication center", "Protein ribosome translation center", "Selective nutrient barrier"],
    "nucleus gene replication": ["Genetic DNA replication center", "ATP energy respiration center", "Protein translation ribosomes center", "Lysosome waste digestor"],
    "ribosome protein translation": ["Protein translation messenger RNA", "DNA gene replication center", "Cellular ATP energy center", "Selective waste digestor"],
    "lysosome waste digestion": ["Enzymatic waste digestor organelle", "Selective membrane barrier walls", "Ribosome protein translation center", "Gene replication center"],
    "membrane selective permeability": ["Selective nutrient barrier walls", "Enzymatic waste digestor fields", "Respiration ATP energy center", "DNA gene replication"],
    "trophic level energy": ["Ten percent energy transfer", "Continuous energy flow recycling", "Predator species count growth", "Biomass decomposition speed"],
    "food web interaction": ["Interlinked network species interactions", "Linear chain sequence transfers", "Carrying capacity maximum limits", "Nitrogen cycle steps"],
    "carrying capacity limit": ["Maximum sustainable habitat population", "Minimum species survival rate", "Food web network interactions", "Trophic level count"],
    "nitrogen fixationBase": ["Microbial ammonia conversion", "Photosynthetic energy conversion", "Decomposition decay fields", "Food web paths"],
    "nitrogen fixation bacteria": ["Microbial ammonia gas conversion", "Photosynthetic energy synthesis conversions", "Decomposition biomass decay fields", "Food web paths"],
    "biodiversity species resilience": ["Ecosystem stability species richness", "Trophic level energy transfer", "Habitat carrying capacity limits", "Nitrogen cycle flows"],

    # ENGLISH
    "modifiers placement": ["Ambiguous target modification", "Clear subject modification", "Verb clause coordination", "Sentence splicing"],
    "dangling modifiers": ["Missing target modifier subject", "Clear target modifier subject", "Improper adjective split", "Pronoun coordinate"],
    "subject implied": ["Incorrectly assuming implied actors", "Specifying clear active actors", "Passive voice sentences", "Coordinate verb joins"],
    "corrections": ["Inserting active actors subjects", "Removing description clauses", "Joining coordinate sentences", "Truncating descriptive words"],
    "synonym inference clues": ["Contextual meaning equivalence signals", "Antonym contrast word signals", "Etymological root origins analysis", "Homophone spelling distinction"],
    "antonym contrast signals": ["Contrast indicators showing opposite", "Equivalence indicators showing synonym", "Etymological root origins analysis", "Homophone spelling lines"],
    "metaphorical language intent": ["Non-literal comparison meanings expressions", "Literal structural sentence parsing", "Etymological history analysis", "Homophone spelling checks"],
    "etymology root origins": ["Historical word derivation roots", "Contextual equivalence synonym clues", "Literal structural parsing rules", "Homophone spelling lines"],
    "homophone spelling distinctions": ["Same sound unique spelling", "Same spelling unique sound", "Equivalent contextual synonym clues", "Root origins history"],

    # HISTORY
    "mesopotamian code Hammurabi": ["First written retributive justice", "Senate democratic assembly voting", "Pharaoh absolute rule dynastic", "Free market trading system"],
    "egyptian hierarchy pharaoh": ["Pharaoh absolute rule dynastic", "Written retributive justice codes", "Senate democratic assembly voting", "Free trade routes"],
    "roman republic senate": ["Senate representative patrician council", "Pharaoh absolute rule dynastic", "Written retributive justice codes", "Assembly democratic voting"],
    "silk road trade": ["Eurasian trade network connections", "Written retributive justice codes", "Senate representative council assembly", "Pharaoh rule dynastic"],
    "greek democracy assembly": ["Direct citizen assembly voting", "Senate representative patrician council", "Pharaoh absolute rule dynastic", "Retributive justice codes"],
    "steam engine mechanization": ["Coal powered machinery automation", "Free market capitalism deregulation", "Guild system hand production", "Assembly line assembly"],
    "urbanization labor shifts": ["Rural to city migration", "City to rural migration", "Aviation transport networks growth", "Free market capitalism deregulation"],
    "capitalism free market": ["Private wealth market deregulation", "State ownership guild production", "Pharaoh rule dynastic systems", "Written retributive codes"],
    "factory system division": ["Centralized specialized task division", "Handicraft guild home production", "Senate patrician council systems", "Free market deregulation"],
    "transportation rail network": ["Steam engine rail networks", "Handicraft guild home production", "Rural to city migration", "Pharaoh rule systems"],

    # GEOGRAPHY
    "continental drift theory": ["Supercontinent Pangaea split theory", "Subduction ocean trench folding", "Seismic wave velocity calculation", "Demographic model shifts"],
    "subduction zone trenches": ["Ocean plate sink locations", "Supercontinent Pangaea split lines", "Convergent mountain fold ranges", "Divergent ridge splits"],
    "convergent boundary fold": ["Colliding plate mountain ranges", "Ocean plate sink locations", "Divergent ridge splits systems", "Supercontinent Pangaea splits"],
    "divergent boundary ridge": ["Spreading plate ocean ridges", "Colliding plate mountain ranges", "Ocean plate sink locations", "Seismic wave velocity"],
    "seismic wave propagation": ["Fault line wave velocities", "Spreading plate ocean ridges", "Colliding plate mountain ranges", "Ocean plate sinks"],
    "population density distribution": ["Spatial demographic pattern maps", "Push pull migration factors", "Demographic transition model phases", "Fertility decline trends"],
    "migration push pull": ["Economic conflict job factors", "Spatial demographic pattern maps", "Demographic transition model phases", "Fertility decline trends"],
    "urban sprawl expansion": ["Low density city outward growth", "High density city inward growth", "Push pull migration factors", "Demographic model shifts"],
    "fertility rate decline": ["Drop in birth rates", "Drop in death rates", "Migration job factors", "Spatial demographic maps"],
    "demographic transition model": ["Birth death rate evolution phases", "Drop in birth rates", "Migration job factors", "Low density outward growth"],

    # ECONOMICS
    "market equilibrium price": ["Supply demand intersection coordinates", "Marginal utility value coordinates", "Consumer surplus bounds area", "Inflation index value"],
    "elasticity of demand": ["Price change consumer sensitivity", "Supply demand intersection coordinates", "Marginal utility value coordinates", "Inflation index value"],
    "consumer surplus utility": ["Willingness to pay difference", "Price change consumer sensitivity", "Supply demand intersection coordinates", "Inflation index value"],
    "marginal utility cost": ["Incremental satisfaction benefit unit", "Willingness to pay difference", "Price change consumer sensitivity", "Supply demand intersection"],
    "opportunity cost trade": ["Foregone alternative value choice", "Incremental satisfaction benefit unit", "Willingness to pay difference", "Price change sensitivity"],
    "inflation index purchasing": ["Consumer Price Index change", "GDP output calculation formulas", "Interest rate control levels", "Unemployment metric formulas"],
    "interest rate control": ["Central bank discount rates", "Consumer Price Index change", "GDP output calculation formulas", "Unemployment metric formulas"],
    "gdp output calculation": ["Total national production values", "Consumer Price Index change", "Central bank discount rates", "Unemployment metric formulas"],
    "unemployment rate metric": ["Active job seekers percentage", "Total national production values", "Consumer Price Index change", "Central bank discount rates"],
    "central bank reserve": ["Required bank deposit reserves", "Active job seekers percentage", "Total national production values", "Consumer Price Index change"],

    # PROGRAMMING
    "list comprehension syntax": ["Inline Python list creation", "Generator yield memory blocks", "Decorator function wrapper syntax", "OOP interface class"],
    "generator yield memory": ["Lazy yield memory values", "Inline Python list creation", "Decorator function wrapper syntax", "OOP interface class"],
    "decorator function wrapping": ["Wrapper modification function closures", "Lazy yield memory values", "Inline Python list creation", "OOP interface class"],
    "dynamically typed variable": ["Runtime variable type binding", "Lazy yield memory values", "OOP interface class contracts", "Inline Python list creation"],
    "gil concurrency constraint": ["Single thread execution locks", "Runtime variable type binding", "Lazy yield memory values", "OOP interface class"],
    "polymorphism runtime method": ["Runtime method override dispatch", "Class interface implementation contracts", "Private field encapsulation bounds", "Pointer memory release"],
    "inheritance class hierarchy": ["Subclass parent class reuse", "Runtime method override dispatch", "Private field encapsulation bounds", "Pointer memory release"],
    "encapsulation private fields": ["Private fields public getters", "Subclass parent class reuse", "Runtime method override dispatch", "Pointer memory release"],
    "abstraction interface contracts": ["Class interface implementation contracts", "Private fields public getters", "Subclass parent class reuse", "Pointer memory release"],
    "garbage collection sweep": ["Automatic memory sweep sweeps", "Class interface implementation contracts", "Private fields public getters", "Subclass parent class reuse"],
    "raw pointers memory": ["Direct memory address keys", "Reference variable aliases", "Virtual table dispatch systems", "Smart pointer unique objects"],
    "smart pointers unique": ["Automatic memory unique owners", "Direct memory address keys", "Reference variable aliases", "Virtual table dispatch systems"],
    "reference variable alias": ["Alternative variable memory alias", "Automatic memory unique owners", "Direct memory address keys", "Virtual table dispatch systems"],
    "destructor memory release": ["Explicit class memory release", "Alternative variable memory alias", "Automatic memory unique owners", "Direct memory address keys"],
    "virtual table dispatch": ["Dynamic binding dispatch tables", "Explicit class memory release", "Alternative variable memory alias", "Automatic memory unique owners"],

    # DBMS
    "inner join intersect": ["Matching rows intersection keys", "Left row matching keys", "Cartesian product rows matrix", "Aggregate group group boundaries"],
    "left outer join": ["Left rows matching keys", "Matching rows intersection keys", "Cartesian product rows matrix", "Aggregate group group boundaries"],
    "cross join product": ["Cartesian product rows matrix", "Left rows matching keys", "Matching rows intersection keys", "Aggregate group group boundaries"],
    "group by aggregate": ["Aggregate group group boundaries", "Cartesian product rows matrix", "Left rows matching keys", "Matching rows intersection keys"],
    "subquery execution order": ["Nested query execution steps", "Aggregate group group boundaries", "Cartesian product rows matrix", "Left rows matching keys"],
    "first normal form": ["Atomic value columns tables", "Partial dependency removal steps", "Transitive dependency removal steps", "Multi-valued dependency keys"],
    "second normal form": ["Partial dependency removal steps", "Atomic value columns tables", "Transitive dependency removal steps", "Multi-valued dependency keys"],
    "third normal form": ["Transitive dependency removal steps", "Partial dependency removal steps", "Atomic value columns tables", "Multi-valued dependency keys"],
    "boyce codd form": ["Superkey dependency validation rules", "Transitive dependency removal steps", "Partial dependency removal steps", "Atomic value columns tables"],
    "functional dependency key": ["Determinant key attribute maps", "Superkey dependency validation rules", "Transitive dependency removal steps", "Partial dependency removal steps"],

    # OS
    "context switching overhead": ["CPU state saving overhead", "CPU scheduler queue scheduling", "Round robin time slice", "Deadlock condition prevention"],
    "cpu scheduler dispatch": ["Process selector dispatch queue", "CPU state saving overhead", "Round robin time slice", "Deadlock condition prevention"],
    "round robin time slice": ["Fixed execution time slice", "Process selector dispatch queue", "CPU state saving overhead", "Deadlock condition prevention"],
    "deadlock prevention conditions": ["Mutual exclusion hold wait", "Fixed execution time slice", "Process selector dispatch queue", "CPU state saving overhead"],
    "semaphore thread sync": ["Integer value thread synchronizers", "Mutual exclusion hold wait", "Fixed execution time slice", "Process selector dispatch queue"],
    "virtual memory mapping": ["Virtual physical address translations", "Page fault hard disk", "Translation lookaside buffer caches", "Internal fragmentation size"],
    "page fault swap": ["Page fault hard disk", "Virtual physical address translations", "Translation lookaside buffer caches", "Internal fragmentation size"],
    "tlb translation cache": ["Translation lookaside buffer caches", "Page fault hard disk", "Virtual physical address translations", "Internal fragmentation size"],
    "fragmentation internal external": ["Unused memory spaces wastage", "Translation lookaside buffer caches", "Page fault hard disk", "Virtual physical address translations"],
    "lru page replacement": ["Least recently used replacement", "Unused memory spaces wastage", "Translation lookaside buffer caches", "Page fault hard disk"],

    # CN
    "three way handshake": ["SYN SYN-ACK ACK handshake", "TCP window flow control", "Subnet IP address mask", "Domain name lookup index"],
    "sliding window control": ["TCP window flow control", "SYN SYN-ACK ACK handshake", "Subnet IP address mask", "Domain name lookup index"],
    "ip routing subnet": ["Subnet IP address mask", "TCP window flow control", "SYN SYN-ACK ACK handshake", "Domain name lookup index"],
    "dns name resolution": ["Domain name lookup index", "Subnet IP address mask", "TCP window flow control", "SYN SYN-ACK ACK handshake"],
    "dhcp address lease": ["IP address lease allocation", "Domain name lookup index", "Subnet IP address mask", "TCP window flow control"],

    # ML
    "gradient descent steps": ["Error minimization descent steps", "Model bias overfitting errors", "Weight L1 L2 regularization", "Precision recall metrics"],
    "overfitting model bias": ["Model bias overfitting errors", "Error minimization descent steps", "Weight L1 L2 regularization", "Precision recall metrics"],
    "regularization l1 l2": ["Weight L1 L2 regularization", "Model bias overfitting errors", "Error minimization descent steps", "Precision recall metrics"],
    "precision recall f1": ["Precision recall metrics", "Weight L1 L2 regularization", "Model bias overfitting errors", "Error minimization descent steps"],
    "decision tree splits": ["Feature entropy splits criteria", "Precision recall metrics", "Weight L1 L2 regularization", "Model bias overfitting errors"],

    # AI
    "minimax adversarial search": ["Adversarial state valuation tree", "Alpha beta state prune", "A star heuristic path", "Genetic crossovers mutations"],
    "alpha beta pruning": ["Alpha beta state prune", "Adversarial state valuation tree", "A star heuristic path", "Genetic crossovers mutations"],
    "a star distance": ["A star heuristic path", "Alpha beta state prune", "Adversarial state valuation tree", "Genetic crossovers mutations"],
    "heuristic evaluation cost": ["Adversarial state cost estimations", "A star heuristic path", "Alpha beta state prune", "Adversarial state valuation tree"],
    "genetic algorithm crossover": ["Genetic crossovers mutations", "Adversarial state cost estimations", "A star heuristic path", "Alpha beta state prune"],

    # APTITUDE
    "compound interest growth": ["Exponential interest growth scales", "Ratio scale proportion calculations", "Relative velocity distance formulas", "Permutations combinations counting"],
    "ratio proportion scales": ["Ratio scale proportion calculations", "Exponential interest growth scales", "Relative velocity distance formulas", "Permutations combinations counting"],
    "speed distance relative": ["Relative velocity distance formulas", "Ratio scale proportion calculations", "Exponential interest growth scales", "Permutations combinations counting"],
    "permutation arrangement count": ["Permutations combinations counting", "Relative velocity distance formulas", "Ratio scale proportion calculations", "Exponential interest growth scales"],
    "probability outcomes sample": ["Target sample outcomes probability", "Permutations combinations counting", "Relative velocity distance formulas", "Ratio scale proportion calculations"]
}

# ==========================================
# DIFFICULTY RULES
# ==========================================

def get_diff(qtype):
    return {
        "memory": "easy",
        "conceptual": "medium",
        "tricky": "medium",
        "application": "hard",
        "reasoning": "hard"
    }[qtype]

# ==========================================
# QUESTION BUILDER ENGINE WITH TEMPLATE LISTS
# ==========================================

PROMPT_TEMPLATES = {
    "memory": [
        "What is the primary definition of {concept}?",
        "Which of the following describes the fundamental nature of {concept}?",
        "Identify the key characteristic that defines {concept}."
    ],
    "conceptual": [
        "What is the underlying theoretical principle behind {concept}?",
        "Why is {concept} considered a foundational element in this domain?",
        "How does {concept} conceptually distinguish itself from related terms?"
    ],
    "tricky": [
        "Which statement represents a common misconception about {concept}?",
        "Which of the following is NOT true regarding {concept}?",
        "What is a subtle pitfall when dealing with {concept}?"
    ],
    "application": [
        "In a production scenario, how is {concept} practically applied?",
        "Which of the following is a direct real-world application of {concept}?",
        "How would a practitioner implement {concept} to solve standard problems?"
    ],
    "reasoning": [
        "What is the logical consequence or impact of modifying {concept}?",
        "Analyze the trade-offs and structural implications of using {concept}.",
        "Under what conditions would {concept} yield the most optimal result?"
    ]
}

def generate_question(concept, variant_index=0):
    base_options = OPTION_BANK.get(concept, ["Correct Option", "Trap Option 1", "Trap Option 2", "Trap Option 3"])
    correct_answer = base_options[0]

    # Generate different option shuffles for variance
    options = base_options.copy()
    if variant_index > 0:
        # Swap some elements to create different correctIndex for duplicate prevention
        options[1], options[2] = options[2], options[1]
    
    random.seed(hash(concept) + variant_index)
    random.shuffle(options)

    correct_index = options.index(correct_answer)
    wrong_index = random.choice([i for i in range(4) if i != correct_index])

    questions_list = []
    
    # 5 cognitive types
    for qtype, templates in PROMPT_TEMPLATES.items():
        template = templates[variant_index % len(templates)]
        prompt = template.format(concept=concept)
        
        # tricky correct index is wrong index
        corr = wrong_index if qtype == "tricky" else correct_index
        
        questions_list.append({
            "type": qtype,
            "prompt": prompt,
            "options": options,
            "correct": corr
        })
        
    return questions_list

# ==========================================
# INSERT LOGIC
# ==========================================

def insert_to_db(cur, s, t, st, q):
    # Duplicate check
    cur.execute("""
        SELECT id FROM question_bank 
        WHERE prompt = ? AND option_a = ? AND option_b = ?
    """, (q["prompt"], q["options"][0], q["options"][1]))
    
    if cur.fetchone():
        return False

    # Generate semantic and variant IDs
    semantic_id = generate_semantic_id(st, q["type"])
    variant_id = generate_variant_id(st, q["type"], q["prompt"])

    cur.execute("""
        INSERT INTO question_bank (
            subject, topic, subtopic, difficulty, cognitive_type,
            prompt, option_a, option_b, option_c, option_d,
            correct_index, semantic_id, variant_id, created_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Approved')
    """, (
        s, t, st, get_diff(q["type"]), q["type"],
        q["prompt"], q["options"][0], q["options"][1], q["options"][2], q["options"][3],
        q["correct"], semantic_id, variant_id, datetime.now().isoformat()
    ))
    return True

# ==========================================
# RUN SEED GENERATOR
# ==========================================

def run_generator(count_per_concept=3):
    conn = get_conn()
    cur = conn.cursor()
    
    total = 0
    # Generate count_per_concept variants per concept to expand pool
    for (s, t, st), concepts in MASTER_MAP.items():
        for concept in concepts:
            for variant_idx in range(count_per_concept):
                qlist = generate_question(concept, variant_idx)
                for q in qlist:
                    if insert_to_db(cur, s, t, st, q):
                        total += 1
                        
    conn.commit()
    conn.close()
    print(f"Unified Question Generator Completed. Added {total} questions to Database.")

if __name__ == "__main__":
    run_generator()