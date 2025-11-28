"""Known SAS function names.

This module contains a comprehensive list of SAS functions to distinguish
function calls from field references during parsing and extraction.
"""

# Common SAS functions - used to filter out function names from field extraction
SAS_FUNCTIONS: frozenset[str] = frozenset({
    # String functions
    "cat", "cats", "catt", "catx", "catq",
    "compress", "compbl",
    "index", "indexc", "indexw",
    "input", "put",
    "left", "right", "trim", "strip",
    "length", "lengthn", "lengthc", "lengthm",
    "lowcase", "upcase", "propcase",
    "reverse", "translate", "tranwrd", "transtrn",
    "scan", "substr", "substrn",
    "verify", "find", "findc", "findw",
    "quote", "dequote",
    "repeat", "reverse",
    "soundex", "spedis",
    "anyalnum", "anyalpha", "anydigit", "anypunct", "anyspace",
    "notalnum", "notalpha", "notdigit", "notpunct", "notspace",
    "coalescec", "countc", "countw",
    "prxmatch", "prxparse", "prxchange", "prxposn",
    "md5", "sha256",

    # Numeric functions
    "abs", "ceil", "floor", "int", "round", "trunc",
    "mod", "sign",
    "sqrt", "exp", "log", "log10", "log2",
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
    "sinh", "cosh", "tanh",
    "min", "max", "sum", "mean", "std", "var",
    "n", "nmiss", "cmiss", "missing", "coalesce",
    "range", "iqr", "median",
    "rand", "ranuni", "rannor", "ranbin", "ranpoi",
    "byte", "rank",
    "constant", "fact", "gamma", "lgamma", "digamma",
    "comb", "perm",
    "gcd", "lcm",

    # Date and time functions
    "date", "today", "datetime", "time", "dhms", "hms",
    "mdy", "yrdif", "datdif",
    "year", "month", "day", "weekday", "qtr", "week",
    "hour", "minute", "second",
    "intck", "intnx",
    "datepart", "timepart",
    "juldate", "juldate7",

    # Date/time formatting functions
    "put", "input",

    # Statistical functions
    "probnorm", "probt", "probf", "probchi", "probbnml",
    "quantile", "tinv", "finv", "cinv",
    "betainv", "gaminv",
    "cdf", "pdf", "sdf", "logcdf", "logpdf", "logsdf",
    "ordinal", "pctl", "largest", "smallest",

    # Financial functions
    "compound", "daccdb", "daccdbsl", "daccsl", "daccsyd",
    "dacctab", "depdb", "depdbsl", "depsl", "depsyd",
    "deptab", "intrr", "irr", "mort", "netpv", "npv",
    "pmt", "pvp", "saving",

    # Array functions
    "dim", "hbound", "lbound",
    "whichn", "whichc",

    # Variable information functions
    "vname", "vlabel", "vformat", "vinformat", "vtype", "vlength",
    "vvalue", "vartype", "varlen", "varnum", "varname", "varlabel",
    "varfmt", "varinfmt",
    "nvar", "nobs",

    # Character-numeric conversion
    "input", "put", "inputn", "inputc", "putn", "putc",

    # Comparison functions
    "ifc", "ifn", "choose", "choosec", "choosen",

    # Logical functions
    "verify", "missing", "notdigit",

    # Macro-related functions (used in data step)
    "symget", "symexist", "symglobl", "symlocal",
    "resolve", "call symput", "call symputx",

    # Special functions
    "lag", "lag1", "lag2", "lag3", "lag4", "lag5", "lag6", "lag7", "lag8", "lag9",
    "lag10", "lag11", "lag12",
    "dif", "dif1", "dif2", "dif3", "dif4", "dif5",
    "first", "last",
    "retain",

    # I/O functions
    "fileexist", "fexist", "filename", "finfo", "fopen", "fclose",
    "fread", "fwrite", "fget", "fput", "frewind",
    "pathname", "libname", "libref",

    # Utility functions
    "sleep", "wakeup",
    "getoption", "datetime",
    "sysget", "sysmsg", "sysrc",
    "system",
    "monotonic",

    # SAS/STAT functions
    "probit", "logit",

    # Data step functions that look like keywords
    "eof", "error", "exist",

    # Aggregate/summary functions (often in PROC SQL)
    "count", "avg", "sum", "min", "max", "var", "std",
    "nmiss", "n", "uss", "css", "cv", "t", "prt",
    "stderr", "range", "median", "mode",
    "freq", "monotonic",
})


def is_sas_function(name: str) -> bool:
    """Check if a name is a known SAS function.

    Args:
        name: The identifier to check.

    Returns:
        True if the name is a known SAS function.
    """
    return name.lower() in SAS_FUNCTIONS
