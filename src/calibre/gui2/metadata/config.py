#!/usr/bin/env python2
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2011, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import textwrap

from PyQt5.Qt import (QWidget, QGridLayout, QGroupBox, QListView, Qt, QSpinBox,
        QDoubleSpinBox, QCheckBox, QLineEdit, QComboBox, QLabel)

from calibre.gui2.preferences.metadata_sources import FieldsModel as FM

class FieldsModel(FM):  # {{{

    def __init__(self, plugin):
        FM.__init__(self)
        self.plugin = plugin
        self.exclude = frozenset(['title', 'authors']) | self.exclude
        self.prefs = self.plugin.prefs

    def initialize(self):
        fields = self.plugin.touched_fields
        self.beginResetModel()
        self.fields = []
        for x in fields:
            if not x.startswith('identifier:') and x not in self.exclude:
                self.fields.append(x)
        self.fields.sort(key=lambda x:self.descs.get(x, x))
        self.endResetModel()

    def state(self, field, defaults=False):
        src = self.prefs.defaults if defaults else self.prefs
        return (Qt.Unchecked if field in src['ignore_fields']
                    else Qt.Checked)

    def restore_defaults(self):
        self.beginResetModel()
        self.overrides = dict([(f, self.state(f, True)) for f in self.fields])
        self.endResetModel()

    def commit(self):
        ignored_fields = set([x for x in self.prefs['ignore_fields'] if x not in
            self.overrides])
        changed = set([k for k, v in self.overrides.iteritems() if v ==
            Qt.Unchecked])
        self.prefs['ignore_fields'] = list(ignored_fields.union(changed))

# }}}

class ConfigWidget(QWidget):

    def __init__(self, plugin):
        QWidget.__init__(self)
        self.plugin = plugin

        self.l = l = QGridLayout()
        self.setLayout(l)

        self.gb = QGroupBox(_('Downloaded metadata fields'), self)
        if plugin.config_help_message:
            self.pchm = QLabel(plugin.config_help_message)
            self.pchm.setWordWrap(True)
            self.pchm.setOpenExternalLinks(True)
            l.addWidget(self.pchm, 0, 0, 1, 2)
        l.addWidget(self.gb, l.rowCount(), 0, 1, 2)
        self.gb.l = QGridLayout()
        self.gb.setLayout(self.gb.l)
        self.fields_view = v = QListView(self)
        self.gb.l.addWidget(v, 0, 0)
        v.setFlow(v.LeftToRight)
        v.setWrapping(True)
        v.setResizeMode(v.Adjust)
        self.fields_model = FieldsModel(self.plugin)
        self.fields_model.initialize()
        v.setModel(self.fields_model)

        self.memory = []
        self.widgets = []
        for opt in plugin.options:
            self.create_widgets(opt)

    def create_widgets(self, opt):
        val = self.plugin.prefs[opt.name]
        if opt.type == 'number':
            c = QSpinBox if isinstance(opt.default, int) else QDoubleSpinBox
            widget = c(self)
            widget.setValue(val)
        elif opt.type == 'string':
            widget = QLineEdit(self)
            widget.setText(val if val else '')
        elif opt.type == 'bool':
            widget = QCheckBox(opt.label, self)
            widget.setChecked(bool(val))
        elif opt.type == 'choices':
            widget = QComboBox(self)
            for key, label in opt.choices.iteritems():
                widget.addItem(label, (key))
            idx = widget.findData((val))
            widget.setCurrentIndex(idx)
        widget.opt = opt
        widget.setToolTip(textwrap.fill(opt.desc))
        self.widgets.append(widget)
        r = self.l.rowCount()
        if opt.type == 'bool':
            self.l.addWidget(widget, r, 0, 1, self.l.columnCount())
        else:
            l = QLabel(opt.label)
            l.setToolTip(widget.toolTip())
            self.memory.append(l)
            l.setBuddy(widget)
            self.l.addWidget(l, r, 0, 1, 1)
            self.l.addWidget(widget, r, 1, 1, 1)

    def commit(self):
        self.fields_model.commit()
        for w in self.widgets:
            if isinstance(w, (QSpinBox, QDoubleSpinBox)):
                val = w.value()
            elif isinstance(w, QLineEdit):
                val = unicode(w.text())
            elif isinstance(w, QCheckBox):
                val = w.isChecked()
            elif isinstance(w, QComboBox):
                idx = w.currentIndex()
                val = unicode(w.itemData(idx) or '')
            self.plugin.prefs[w.opt.name] = val


