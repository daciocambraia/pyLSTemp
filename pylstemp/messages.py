"""Public API error context, preserving existing exception classes."""
from functools import wraps
from inspect import signature
from .exceptions import PyLandTempError
from .requirements import INPUT_HELP

def contextual_errors(function):
    """Attach workflow/selector names and next actions to input errors."""
    contract=signature(function)
    @wraps(function)
    def wrapped(*args,**kwargs):
        bound=None
        try:
            bound=contract.bind(*args,**kwargs)
            bound.apply_defaults()
            return function(*args,**kwargs)
        except (PyLandTempError,ValueError,TypeError) as exc:
            selectors=[]
            if bound is not None:
                for key in ("index","lst_method","emissivity_method","method","band","sensor","kind","input_quantity"):
                    if key in bound.arguments:
                        value=repr(bound.arguments[key])
                        selectors.append(key+"="+(value if len(value)<100 else value[:97]+"..."))
            context=function.__name__+"("+", ".join(selectors)+")"
            help_text=INPUT_HELP.get(function.__name__,"Check input shapes, units and method requirements.")
            if bound is None:help_text="Call "+function.__name__+str(contract)+"."
            # Keep nested workflow context, but present the next action once.
            suffix = "" if getattr(exc, "_pylstemp_input_help", False) else " "+help_text
            contextual = type(exc)(context+": "+str(exc)+suffix)
            contextual._pylstemp_input_help = True
            raise contextual from exc
    return wrapped
