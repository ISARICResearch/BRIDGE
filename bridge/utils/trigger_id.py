def get_trigger_id(ctx):
    # Check which input triggered the callback
    if not ctx.triggered:
        trigger_id = 'No clicks yet'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return trigger_id
