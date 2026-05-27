from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget


def animate_fade(widget: QWidget, start: float = 0.0, end: float = 1.0, duration: int = 180):
    if QGraphicsOpacityEffect is None or QPropertyAnimation is None:
        return None
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(start)
    animation = QPropertyAnimation(effect, b'opacity', widget)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._fade_animation = animation
    return animation


def fade_out_and_close(widget: QWidget, duration: int = 160):
    if QGraphicsOpacityEffect is None or QPropertyAnimation is None:
        widget.close()
        return None
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(1.0)
    animation = QPropertyAnimation(effect, b'opacity', widget)
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.finished.connect(widget.accept if hasattr(widget, 'accept') else widget.close)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._fade_close_animation = animation
    return animation


def animate_stack_switch(stack: QStackedWidget, index: int):
    current_index = stack.currentIndex()
    if index < 0 or index == current_index:
        return
    stack.setCurrentIndex(index)
    page = stack.currentWidget()
    if page is None:
        return
    if QPropertyAnimation is None:
        return
    end_pos = page.pos()
    offset = 100 if index > current_index else -100
    start_pos = QPoint(end_pos.x(), end_pos.y() + offset)
    page.move(start_pos)
    move = QPropertyAnimation(page, b'pos', page)
    move.setDuration(600)
    move.setStartValue(start_pos)
    move.setEndValue(end_pos)
    move.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade = animate_fade(page, 0.35, 1.0, 350)
    move.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    page._slide_animation = (move, fade)


def pulse_widget(widget: QWidget, duration: int = 150):
    if QPropertyAnimation is None:
        return None
    original = widget.geometry()
    grown = original.adjusted(-2, -2, 2, 2)
    grow = QPropertyAnimation(widget, b'geometry', widget)
    grow.setDuration(duration)
    grow.setStartValue(original)
    grow.setEndValue(grown)
    grow.setEasingCurve(QEasingCurve.Type.OutCubic)
    shrink = QPropertyAnimation(widget, b'geometry', widget)
    shrink.setDuration(duration)
    shrink.setStartValue(grown)
    shrink.setEndValue(original)
    shrink.setEasingCurve(QEasingCurve.Type.OutCubic)
    group = QParallelAnimationGroup(widget)
    grow.finished.connect(shrink.start)
    group.addAnimation(grow)
    group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)
    widget._pulse_animation = (group, shrink)
    return group
