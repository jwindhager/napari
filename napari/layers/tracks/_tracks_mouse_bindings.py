def interact(layer, event):
    """
    TODO
    """
    if len(event.modifiers) == 1:
        if event.modifiers[0] == 'Shift':
            layer.add(event.position, layer._current_track_id)

        elif event.modifiers[0] == 'Alt':
            selected = layer.select(event.position)
            if selected is not None:
                layer.remove(selected)

        elif event.modifiers[0] == 'Control':
            selected = layer.select(event.position)
            if selected is None:
                return
            yield

            while event.type == 'mouse_move':
                layer.move(selected, event.position)
                yield

    elif len(event.modifiers) == 2:
        if 'Shift' in event.modifiers and 'Control' in event.modifiers:
            selected = layer.select(event.position)

            if layer._selected_data is None:
                layer._selected_data = selected
            elif selected is not None:
                layer.join(layer._selected_data, selected)
