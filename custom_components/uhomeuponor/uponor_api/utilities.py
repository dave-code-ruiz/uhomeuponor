def flatten(*args):
    output = []
    for arg in args:
        if hasattr(arg, '__iter__'):
            output.extend(flatten(*arg))
        else:
            output.append(arg)
    return output

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]