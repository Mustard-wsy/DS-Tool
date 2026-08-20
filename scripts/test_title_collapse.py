"""Regression test: hiding a node's __title__ pseudo-field must collapse the
vertical title column in the serialized payload (titleColW: 0), not leave the
natural header width behind.

Run:  e:/Study/DataStructure/DSVis/.venv/bin/python.exe scripts/test_title_collapse.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dsvis.card_renderer import build_g6_data

NODE = {
    'id': 1,
    'class_name': 'AVLNode',
    'label': 'node\n(AVLNode)',
    'rows': [
        {'text': 'key: 30', 'kind': 'value'},
        {'text': 'left', 'kind': 'ref'},
        {'text': 'right', 'kind': 'ref'},
        {'text': 'height: 4', 'kind': 'value'},
    ],
}
EDGES = []
LAYOUT_V = {'type': 'dagre', 'rankdir': 'TB'}


def _title_col_w(data):
    return data['nodes'][0]['style']['titleColW']


def test_title_visible_keeps_width():
    data = build_g6_data([NODE], EDGES, LAYOUT_V, text_flow='vertical',
                         field_visibility={'AVLNode.__title__': 'visible'})
    w = _title_col_w(data)
    assert w > 0, f"expected a positive titleColW when title visible, got {w}"
    print(f"[PASS] title visible → titleColW={w}")


def test_title_hidden_collapses_to_zero():
    data = build_g6_data([NODE], EDGES, LAYOUT_V, text_flow='vertical',
                         field_visibility={'AVLNode.__title__': 'self'})
    w = _title_col_w(data)
    assert w == 0, f"expected titleColW==0 when __title__ hidden, got {w}"
    # Card width must drop the title column (2×10 padding + 4 field columns).
    # fieldColW itself scales with char_px, so assert against the serialized
    # fieldColW rather than a hard-coded number.
    style = data['nodes'][0]['style']
    expected_w = 20 + 4 * style['fieldColW']
    size = style['size']
    assert size[0] == expected_w, f"card width should collapse with title, got {size[0]} expected {expected_w}"
    print(f"[PASS] title hidden → titleColW={w}, size={size}")


def test_other_type_title_unaffected():
    """Hiding AVLNode.__title__ must not collapse AVLTree's title."""
    tree = {'id': 2, 'class_name': 'AVLTree', 'label': 'avl\n(AVLTree)',
            'rows': [{'text': 'root', 'kind': 'ref'}]}
    data = build_g6_data([NODE, tree], EDGES, LAYOUT_V, text_flow='vertical',
                         field_visibility={'AVLNode.__title__': 'self'})
    by_id = {n['id']: n['style'] for n in data['nodes']}
    assert by_id['1']['titleColW'] == 0
    assert by_id['2']['titleColW'] > 0, "AVLTree title must stay visible"
    print(f"[PASS] scope respected: AVLNode→0, AVLTree→{by_id['2']['titleColW']}")


def test_horizontal_unaffected():
    data = build_g6_data([NODE], EDGES, None, text_flow='horizontal',
                         field_visibility={'AVLNode.__title__': 'self'})
    assert data['nodes'][0]['style']['titleColW'] == 0  # horizontal never sets it
    print('[PASS] horizontal layout unaffected')


if __name__ == '__main__':
    test_title_visible_keeps_width()
    test_title_hidden_collapses_to_zero()
    test_other_type_title_unaffected()
    test_horizontal_unaffected()
    print('\nAll title-collapse tests passed.')
