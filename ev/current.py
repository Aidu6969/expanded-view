"""Shared state for the episode being built. ev.build sets these BEFORE importing the episode's scene.py,
so scene.py can do `from ev.current import tl` and compute its cue times at import."""
tl = None        # ev.timeline.Timeline
ep = None        # the episode module (episode.py)
t_end = None     # end card (punchline) starts
t_topic = None   # big topic title appears
hook_out = None  # hook title leaves


def ending_k(t, dur=0.6):
    """0 -> 1 as the end card takes over. Episodes fade/shrink their content with this."""
    from .gfx import ease, lin
    return ease(lin(t, t_end, t_end + dur))
