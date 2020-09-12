import os


def text_from_template(tpl, tpl_parms=None):
    """Substitute all placeholders in a template string with the parameters provided.

    Parameters
    ----------
    tpl: str
        String with placeholders
    tpl_parms: dict
        Dictionary with replacement strings for placeholders
        in the template string.
        Example: {'__FIRST_NAME__': 'Joe', '__LAST_NAME__': 'Doe'}
        Default: {}

    Returns
    -------
    tpl: str
        template where all placeholders have been replaced

    Raises
    ------
    Exception
        If one or more of the template parameters are not found in
        the template string
    """
    if tpl_parms is not None:
        if tpl is None:
            raise Exception('Template is None. Cannot replace anything')
        for placeholder in tpl_parms.keys():
            if placeholder not in tpl:
                raise Exception('Placeholder {} is not found in template'.format(placeholder))
            else:
                tpl = tpl.replace(placeholder, str(tpl_parms[placeholder]))
    return tpl


def text_from_template_file(tpl_file, tpl_parms=None):
    """Substitute all placeholders in a template file with the parameters provided.
    
    Parameters
    ----------
    tpl_file: str
        Path to a template file
    tpl_parms: dict
        Dictionary with replacement strings for placeholders
        in the template string.
        Example: {'__FIRST_NAME__': 'Joe', '__LAST_NAME__': 'Doe'}
        Default: {}

    Returns
    -------
    tpl: str
        Template where all placeholders have been replaced

    Raises
    ------
    Exception
        If one or more of the template parameters are not found in the template string
    """
    if os.path.isfile(tpl_file):
        with open(tpl_file, 'r') as f:
            tpl = f.read()
            return text_from_template(tpl, tpl_parms)
    else:
        raise Exception("{} doesn't exist".format(tpl_file))
