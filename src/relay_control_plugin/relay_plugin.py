#!/usr/bin/env python3

import rospy
from rqt_gui_py.plugin import Plugin
from python_qt_binding.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
from std_msgs.msg import String

class RelayControlPlugin(Plugin):

    def __init__(self, context):
        super(RelayControlPlugin, self).__init__(context)
        self.setObjectName('RelayControlPlugin')

        self.sub = None
        self.publisher = None
        self._main_widget = None

        self._setup_ui(context)

    def init_plugin(self, context):
        if self._main_widget:
            title = "Relay Control Panel - CJT Robotics"
            if context.serial_number() > 1:
                title += f" ({context.serial_number()})"
            self._main_widget.setWindowTitle(title)
            self._main_widget.setObjectName(title)

    def _setup_ui(self, context):
        self._main_widget = QWidget()
        main_layout = QVBoxLayout(self._main_widget)

        topic_layout = QHBoxLayout()
        self.label = QLabel("Topic:")
        self.topic_combo = QComboBox()
        self.topic_combo.setEditable(True)
        self.topic_combo.currentIndexChanged.connect(self._reconnect_topic)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Refresh Topics")
        self.refresh_btn.clicked.connect(self._update_topic_list)
        
        topic_layout.addWidget(self.label)
        topic_layout.addWidget(self.topic_combo, stretch=1)
        topic_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(topic_layout)
        btn_layout = QHBoxLayout()
        self.btn_on = QPushButton("ON")
        self.btn_on.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; font-size: 14px; padding: 12px;")
        self.btn_on.clicked.connect(lambda: self._send_command("on"))

        self.btn_off = QPushButton("OFF")
        self.btn_off.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; font-size: 14px; padding: 12px;")
        self.btn_off.clicked.connect(lambda: self._send_command("off"))

        btn_layout.addWidget(self.btn_on)
        btn_layout.addWidget(self.btn_off)
        main_layout.addLayout(btn_layout)

        self.btn_toggle = QPushButton("TOGGLE")
        self.btn_toggle.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        self.btn_toggle.clicked.connect(lambda: self._send_command("toggle"))
        main_layout.addWidget(self.btn_toggle)

        context.add_widget(self._main_widget)

        self._update_topic_list()
        self._reconnect_topic()

    def save_settings(self, plugin_settings, instance_settings):
        instance_settings.set_value('topic', self.topic_combo.currentText())

    def restore_settings(self, plugin_settings, instance_settings):
        topic = instance_settings.value('topic', '/cam_mount/relay_cmd')
        self.topic_combo.setEditText(topic)
        self._reconnect_topic()

    def _reconnect_topic(self):
            topic_name = self.topic_combo.currentText().strip()
            
            if self.publisher:
                self.publisher.unregister()
                
            if topic_name:
                if not topic_name.startswith('/'):
                    topic_name = '/' + topic_name
                    
                self.publisher = rospy.Publisher(topic_name, String, queue_size=10)

    def _update_topic_list(self):
        import rosgraph
        
        current_text = self.topic_combo.currentText().strip()
        self.topic_combo.blockSignals(True)
        self.topic_combo.clear()
        
        valid_topics = set()
        
        try:
            code, reason, topic_types = rospy.get_master().getTopicTypes()
            
            if code == 1:
                string_topics = {t[0]: t[1] for t in topic_types if t[1] == 'std_msgs/String'}
                
                master_graph = rosgraph.Master(rospy.get_name())
                publishers, subscribers, _ = master_graph.getSystemState()

                active_topic_names = set()
                for topic, _ in publishers:
                    active_topic_names.add(topic)
                for topic, _ in subscribers:
                    active_topic_names.add(topic)

                for topic in active_topic_names:
                    if topic in string_topics:
                        valid_topics.add(topic)
            else:
                rospy.logerr(reason)
                    
        except Exception as e:
            rospy.logerr(e)

        if current_text:
            valid_topics.add(current_text)

        self.topic_combo.addItems(sorted(list(valid_topics)))
        

        index = self.topic_combo.findText(current_text)
        if index >= 0:
            self.topic_combo.setCurrentIndex(index)
        elif self.topic_combo.count() > 0:
            self.topic_combo.setCurrentIndex(0)

        self.topic_combo.blockSignals(False)

    def _send_command(self, cmd_str):
        if self.publisher:
            msg = String()
            msg.data = cmd_str
            self.publisher.publish(msg)

    def shutdown_plugin(self):
        if self.publisher:
            self.publisher.unregister()