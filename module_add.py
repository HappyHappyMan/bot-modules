import importlib

def command_add(bot, user, channel, args):
    """Use this module to add information to the database."""
    args = args.split(" ", 1)

    module = args[0]
    args = args[1]

    print args

    obj = importlib.import_module("modules.module_%s" % (module))
    handler_method = getattr(obj, "_add_%s" % module, None)
    handler_method(bot, user, args)
    return