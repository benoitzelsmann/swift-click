"""Editable gesture thresholds and repetition intervals, saved as one transaction."""
import copy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QGridLayout, QHBoxLayout
from desktop_ui import label,push
from settings import TIMING_DEFAULTS,TIMING_LIMITS
from ui_controls import NumericSpin, number_stepper


class TimingSettings(QFrame):
    def __init__(self, owner):
        super().__init__()
        self.owner=owner
        self.setObjectName('card')
        box=QVBoxLayout(self)
        box.setContentsMargins(26,20,26,20)
        box.setSpacing(10)
        box.addWidget(label('Button timing',size=18))
        grid=QGridLayout()
        grid.setVerticalSpacing(8)
        self.fields={}
        self.steppers={}
        titles={'double_ms':'Double-press window','long_ms':'Long press starts after','hold_ms':'Continuous hold starts after',
                'volume_repeat_ms':'Volume repeat interval','video_repeat_ms':'Video repeat interval'}
        for row,(key,title) in enumerate(titles.items()):
            grid.addWidget(label(title),row,0)
            field=NumericSpin()
            low,high,step=TIMING_LIMITS[key]
            field.setRange(low,high)
            field.setSingleStep(step)
            field.setSuffix(' ms')
            field.setAccessibleName(title)
            controls,down,up=number_stepper(field,title)
            grid.addWidget(controls,row,1,alignment=Qt.AlignmentFlag.AlignRight)
            self.fields[key]=field
            self.steppers[key]=(down,up)
        box.addLayout(grid)
        buttons=QHBoxLayout()
        self.restore=push('Reset timings',self.reset_defaults)
        buttons.addWidget(self.restore)
        buttons.addStretch()
        self.save=push('Save',self.persist,True)
        buttons.addWidget(self.save)
        box.addLayout(buttons)
        self.error=label('','muted')
        self.error.hide()
        box.addWidget(self.error)
        for field in self.fields.values(): field.valueChanged.connect(self.changed)
        self.load(owner.controller.config.get('timings',TIMING_DEFAULTS))

    def values(self):
        return {key:field.value() for key,field in self.fields.items()}

    def load(self, values):
        for field in self.fields.values(): field.blockSignals(True)
        self.fields['hold_ms'].setMinimum(TIMING_LIMITS['hold_ms'][0])
        for key,value in values.items(): self.fields[key].setValue(value)
        for field in self.fields.values(): field.blockSignals(False)
        self.changed()

    def changed(self):
        self.fields['hold_ms'].setMinimum(max(500,self.fields['long_ms'].value()+100))
        for key,field in self.fields.items():
            down,up=self.steppers[key]
            down.setEnabled(field.value()>field.minimum())
            up.setEnabled(field.value()<field.maximum())
        self.save.setEnabled(self.values()!=self.owner.controller.config.get('timings',TIMING_DEFAULTS))
        self.error.hide()

    def reset_defaults(self):
        self.load(TIMING_DEFAULTS)

    def persist(self):
        cfg=copy.deepcopy(self.owner.controller.config)
        cfg['timings']=self.values()
        try:
            self.owner.controller.save(cfg)
            self.changed()
        except (ValueError,OSError) as exc:
            self.error.setText(str(exc))
            self.error.show()
