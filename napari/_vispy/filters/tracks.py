from typing import List, Union

import numpy as np
from vispy.gloo import VertexBuffer
from vispy.visuals.filters.base_filter import Filter


class TracksFilter(Filter):
    """TracksFilter.

    Custom vertex and fragment shaders for visualizing tracks quickly with
    vispy. The central assumption is that the tracks are rendered as a
    continuous vispy Line segment, with connections and colors defined when
    the visual is created.

    The shader simply changes the visibility and/or fading of the data according
    to the current_time and the associate time metadata for each vertex. This
    is scaled according to the tail and head length. Points ahead of the current time
    are rendered with alpha set to zero.

    Parameters
    ----------
    current_time : int, float
        the current time, which is typically the frame index, although this
        can be an arbitrary float
    tail_length : int, float
        the lower limit on length of the 'tail'
    head_length : int, float
        the upper limit on length of the 'tail'
    use_fade : bool
        this will enable/disable tail fading with time
    vertex_time : 1D array, list
        a vector describing the time associated with each vertex

    TODO
    ----
    - the track is still displayed, albeit with fading, once the track has
     finished but is still within the 'tail_length' window. Should it
     disappear?

    """

    VERT_SHADER = """
        varying vec4 v_track_color;
        varying float v_size;

        void apply_track_shading() {

            float alpha;

            float max_distance = 3;
            // when z is not provided (negative) use very large radius
            float z_distance = ($current_z >= 0 ? max_distance : 1e10);

            float size_factor = 1.0 - abs($current_z - $a_vertex_z) / max_distance;
            v_size = clamp(size_factor, 0.0, 1.0) * v_size;

            if ($a_vertex_time > $current_time + $head_length ||
                ($interactive == 1 && abs($current_z - $a_vertex_z) > z_distance))
             {
                // this is a hack to minimize the frag shader rendering ahead
                // of the current time point due to interpolation
                if ($a_vertex_time <= $current_time + 1){
                    alpha = -100.;
                } else {
                    alpha = 0.;
                }
            } else {
                // fade the track into the temporal distance, scaled by the
                // maximum tail and head length from the gui
                float fade = ($head_length + $current_time - $a_vertex_time) / ($tail_length + $head_length);
                alpha = clamp(1.0-fade, 0.0, 1.0);
            }

            // when use_fade is disabled, the entire track is visible
            if ($use_fade == 0) {
                alpha = 1.0;
            }

            // set the vertex alpha according to the fade
            v_track_color.a = alpha;
        }
    """

    FRAG_SHADER = """
        varying vec4 v_track_color;
        varying float v_size;

        void apply_track_shading() {

            // if the alpha is below the threshold, discard the fragment
            if( v_track_color.a <= 0.0 || v_size <= 0.0) {
                discard;
            }

            // interpolate
            gl_FragColor.a = clamp(v_track_color.a * gl_FragColor.a, 0.0, 1.0);

            // FIXME: not working because lines don't have PointSize;
            // gl_PointSize = v_size;
        }
    """

    def __init__(
        self,
        current_time: Union[int, float] = 0,
        current_z: Union[int, float] = 0,
        tail_length: Union[int, float] = 30,
        head_length: Union[int, float] = 0,
        use_fade: bool = True,
        interactive: bool = False,
        vertex_time: Union[List, np.ndarray] = None,
        vertex_z: Union[List, np.ndarray] = None,
    ):

        super().__init__(
            vcode=self.VERT_SHADER, vpos=3, fcode=self.FRAG_SHADER, fpos=9
        )

        self.current_time = current_time
        self.current_z = current_z
        self.tail_length = tail_length
        self.head_length = head_length
        self.use_fade = use_fade
        self.interactive = interactive
        self.vertex_time = vertex_time
        self.vertex_z = vertex_z

    @property
    def current_time(self) -> Union[int, float]:
        return self._current_time

    @current_time.setter
    def current_time(self, n: Union[int, float]):
        self._current_time = n
        if isinstance(n, slice):
            n = np.max(self._vertex_time)
        self.vshader['current_time'] = float(n)

    @property
    def current_z(self) -> Union[int, float]:
        return self._current_z

    @current_z.setter
    def current_z(self, n: Union[int, float]):
        self._current_z = n
        if n is None:
            # signaling to shader that there is no z
            n = -1
        self.vshader['current_z'] = float(n)

    @property
    def use_fade(self) -> bool:
        return self._use_fade

    @use_fade.setter
    def use_fade(self, value: bool):
        self._use_fade = value
        self.vshader['use_fade'] = float(self._use_fade)

    @property
    def interactive(self) -> bool:
        return self._interactive

    @interactive.setter
    def interactive(self, value: bool):
        self._interactive = value
        self.vshader['interactive'] = float(self._interactive)

    @property
    def tail_length(self) -> Union[int, float]:
        return self._tail_length

    @tail_length.setter
    def tail_length(self, tail_length: Union[int, float]):
        self._tail_length = tail_length
        self.vshader['tail_length'] = float(self._tail_length)

    @property
    def head_length(self) -> Union[int, float]:
        return self._tail_length

    @head_length.setter
    def head_length(self, head_length: Union[int, float]):
        self._head_length = head_length
        self.vshader['head_length'] = float(self._head_length)

    def _attach(self, visual):
        super()._attach(visual)

    @property
    def vertex_time(self):
        return self._vertex_time

    @vertex_time.setter
    def vertex_time(self, v_time):
        self._vertex_time = np.array(v_time).reshape(-1, 1).astype(np.float32)
        self.vshader['a_vertex_time'] = VertexBuffer(self.vertex_time)

    @property
    def vertex_z(self):
        return self._vertex_z

    @vertex_z.setter
    def vertex_z(self, v_z):
        self._vertex_z = np.array(v_z).reshape(-1, 1).astype(np.float32)
        self.vshader['a_vertex_z'] = VertexBuffer(self.vertex_z)
