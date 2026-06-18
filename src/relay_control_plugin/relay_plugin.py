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
        """Setzt den Fenstertitel im CJT-Robotics Design."""
        if self._main_widget:
            title = "Relay Control Panel - CJT Robotics"
            if context.serial_number() > 1:
                title += f" ({context.serial_number()})"
            self._main_widget.setWindowTitle(title)
            self._main_widget.setObjectName(title)

    def _setup_ui(self, context):
        # Haupt-Widget initialisieren
        self._main_widget = QWidget()
        main_layout = QVBoxLayout(self._main_widget)

        # Zeile 1: Topic-Auswahl & Refresh
        topic_layout = QHBoxLayout()
        self.label = QLabel("Topic:")
        self.topic_combo = QComboBox()
        self.topic_combo.setEditable(True)
        self.topic_combo.currentIndexChanged.connect(self._reconnect_topic)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh Topics")
        self.refresh_btn.clicked.connect(self._update_topic_list)
        
        topic_layout.addWidget(self.label)
        topic_layout.addWidget(self.topic_combo, stretch=1)
        topic_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(topic_layout)

        # Zeile 2: Schalter-Buttons (ON / OFF)
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

        # Zeile 3: Toggle Button
        self.btn_toggle = QPushButton("TOGGLE")
        self.btn_toggle.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        self.btn_toggle.clicked.connect(lambda: self._send_command("toggle"))
        main_layout.addWidget(self.btn_toggle)

        # Widget dem RQT-Kontext hinzufügen
        context.add_widget(self._main_widget)
        
        # Initialer Lauf
        self._update_topic_list()
        self._reconnect_topic()

    def save_settings(self, plugin_settings, instance_settings):
        """Speichert das ausgewählte Topic beim Schließen von RQT."""
        instance_settings.set_value('topic', self.topic_combo.currentText())

    def restore_settings(self, plugin_settings, instance_settings):
        """Stellt das ausgewählte Topic nach einem RQT-Neustart wieder her."""
        topic = instance_settings.value('topic', '/cam_mount/relay_cmd')
        self.topic_combo.setEditText(topic)
        self._reconnect_topic()

    def _reconnect_topic(self):
            """Wechselt den Publisher dynamisch auf das ausgewählte Topic."""
            topic_name = self.topic_combo.currentText().strip()
            
            if self.publisher:
                self.publisher.unregister()
                
            if topic_name:
                # FIX: Sicherstellen, dass das Topic absolut (global) ist
                if not topic_name.startswith('/'):
                    topic_name = '/' + topic_name
                    
                # Wir erstellen den Publisher explizit im globalen Namespace
                self.publisher = rospy.Publisher(topic_name, String, queue_size=10)
                rospy.loginfo(f"[RelayControl] Publisher verbunden mit globalem Topic: {topic_name}")

    def _update_topic_list(self):
        """Sucht über den System-State nach ALLEN real existierenden Topics (Pub & Sub) vom Typ std_msgs/String."""
        import rosgraph
        
        current_text = self.topic_combo.currentText().strip()
        self.topic_combo.blockSignals(True)
        self.topic_combo.clear()
        
        valid_topics = set()
        
        try:
            # 1. Alle aktuell registrierten Topic-Typen vom Master holen
            # XML-RPC gibt ein Dreier-Tuple zurück: (code, reason, data)
            code, reason, topic_types = rospy.get_master().getTopicTypes()
            
            if code == 1:  # 1 bedeutet Erfolg bei ROS-Master-Anfragen
                string_topics = {t[0]: t[1] for t in topic_types if t[1] == 'std_msgs/String'}
                
                # 2. Den echten System-State abfragen (Wer publisht, wer subskribiert?)
                master_graph = rosgraph.Master(rospy.get_name())
                publishers, subscribers, _ = master_graph.getSystemState()
                
                # Alle aktiven Topic-Namen aus Pubs und Subs sammeln
                active_topic_names = set()
                for topic, _ in publishers:
                    active_topic_names.add(topic)
                for topic, _ in subscribers:
                    active_topic_names.add(topic)
                    
                # 3. Schnittmenge bilden: Nur aktive Topics, die auch std_msgs/String sind
                for topic in active_topic_names:
                    if topic in string_topics:
                        valid_topics.add(topic)
            else:
                rospy.logerr(f"[RelayControl] Master meldet Fehler beim Topic-Typen-Abruf: {reason}")
                    
        except Exception as e:
            rospy.logerr(f"[RelayControl] Fehler beim Live-Topic-Abruf: {e}")

        # Falls die aktuelle Auswahl existiert, halten wir sie drin
        if current_text:
            valid_topics.add(current_text)

        # Dropdown befüllen
        self.topic_combo.addItems(sorted(list(valid_topics)))
        
        # Vorherige Auswahl wiederherstellen
        index = self.topic_combo.findText(current_text)
        if index >= 0:
            self.topic_combo.setCurrentIndex(index)
        elif self.topic_combo.count() > 0:
            # Falls nichts ausgewählt war, nimm das erste verfügbare
            self.topic_combo.setCurrentIndex(0)
        
        self.topic_combo.blockSignals(False)

    def _send_command(self, cmd_str):
        """Publisht das Kommando."""
        if self.publisher:
            msg = String()
            msg.data = cmd_str
            self.publisher.publish(msg)
        else:
            rospy.logwarn("[RelayControl] Kein aktives Topic zum Senden ausgewählt!")

    def shutdown_plugin(self):
        """Säubert den Publisher beim Schließen."""
        if self.publisher:
            self.publisher.unregister()