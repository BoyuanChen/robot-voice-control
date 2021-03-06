#!/usr/bin/env python

import unittest

import rospy
import rostest
import std_msgs
import genpy

from robot_voice_control.nodes.message_control import LanguageToMessageTranslator


class TestCase(unittest.TestCase):

    def setUp(self):
        self.setupParameters()
        pass

    def setupTranslator(self):
        self.translator = LanguageToMessageTranslator()

    def setupParameters(self):
        self.control_param_name = '/test_topic'

        # Since we cannot access the parameter server directly, fake it by
        # just storing the resulting parameter dictionary here. This is the same
        # as loading the test_params.yaml file and then calling
        # rospy.get_param(/test_topic)
        self.params = {'basic_topic': {'input': 'output',
                                       'input with spaces': 'output with spaces'},
                       'more': {'complicated': {'topic': {'input': 42}}},
                       'not': {'a': {'global': {'topic': {'input': 3.14159}}}},
                       'topics': [{'basic_topic': 'String'},
                                  {'more/complicated/topic': 'Int32'},
                                  {'not/a/global/topic': 'Float32'},
                                  {'unknown_type': 'Unknown'}],
                       'unknown_topic': {'input': 'does not matter'},
                       'unknown_type': {'input': 'does not matter'}}

        # Convert a list of dictionaries to a dictionary.
        self.topics_and_types = dict([x.items()[0] for x in self.params['topics']])

    def testSetup(self):
        self.setupTranslator()
        self.assertIsNotNone(self.translator)
        self.assertIsNotNone(self.translator._nl_command_map)
        self.assertFalse(self.translator._nl_command_map)  # empty
        self.assertIsNotNone(self.translator._publisher_map)
        self.assertFalse(self.translator._publisher_map)  # empty

    def test_parse_command_map_wrong_type(self):
        not_a_type = 'NotAType'
        ret = LanguageToMessageTranslator.parse_command_mapping(
            'topic_name', not_a_type, {'a': 'b'})
        self.assertIsNotNone(ret)

    def test_setup_params(self):
        self.assertEqual(4, len(self.params['topics']))

        # Ensure both relative topics are *under* the params
        self.assertIn('basic_topic', self.params)
        self.assertEqual('String', self.params['topics'][0]['basic_topic'])
        self.assertIn('more', self.params)  # slashes become sub-dicts
        self.assertIn('unknown_type', self.params)
        self.assertIn('unknown_topic', self.params)

        # Basic params
        basic = self.params['basic_topic']
        self.assertEqual(2, len(basic))
        self.assertIn('input', basic)
        self.assertIn('input with spaces', basic)

    def test_topic_types_params(self):
        types_str = [x.values()[0] for x in self.params['topics']]

        types_real = [LanguageToMessageTranslator.string_to_type[x] for x in types_str]

        self.assertEqual(4, len(types_real))
        self.assertIn(None, types_real)
        self.assertIn(std_msgs.msg.Float32, types_real)
        self.assertIn(std_msgs.msg.Int32, types_real)
        self.assertIn(std_msgs.msg.String, types_real)

    def test_parse_command_map_basic(self):
        # Turn the commands defined in 'basic_topic' into a command mapping.
        topic = 'basic_topic'
        topic_type_str = self.topics_and_types[topic]
        commands = self.params[topic]
        ret = LanguageToMessageTranslator.parse_command_mapping(
            topic, topic_type_str, commands)

        self.assertIsNotNone(ret)

        # Should have the same number of elements as commands.
        self.assertEqual(len(commands), len(ret))

        for cmd in commands:  # All commands are in the map
            self.assertIn(cmd, ret)
            # Inspect each tuple: (topic, message)
            x = ret[cmd]
            self.assertEqual(2, len(x))
            self.assertEqual(topic, x[0])
            self.assertIsInstance(x[1], genpy.Message)
            self.assertIsInstance(x[1], std_msgs.msg.String)

        self.assertEqual('output', ret['input'][1].data)
        self.assertEqual('output with spaces', ret['input with spaces'][1].data)

    def test_parse_command_map_unknown_type(self):
        # Same as above, use an unknown message type
        topic = 'unknown_type'
        topic_type_str = self.topics_and_types[topic]
        commands = self.params[topic]
        ret = LanguageToMessageTranslator.parse_command_mapping(
            topic, topic_type_str, commands)

        self.assertIsNotNone(ret)
        self.assertEqual({}, ret)

    def test_get_publisher_string(self):
        topic = 'basic_topic'
        topic_type_str = self.topics_and_types[topic]

        pub_map = LanguageToMessageTranslator.get_publisher(
            topic, topic_type_str)

        self.assertIsNotNone(pub_map)
        self.assertEqual(1, len(pub_map))
        self.assertTrue(topic in pub_map)

        pub = pub_map[topic]
        self.assertIsInstance(pub, rospy.Publisher)
        self.assertEqual('std_msgs/String', pub.type)

    def test_get_publisher_int(self):
        topic = 'more/complicated/topic'
        topic_type_str = self.topics_and_types[topic]

        pub_map = LanguageToMessageTranslator.get_publisher(
            topic, topic_type_str)

        self.assertIsNotNone(pub_map)
        self.assertEqual(1, len(pub_map))
        self.assertTrue(topic in pub_map)

        pub = pub_map[topic]
        self.assertIsInstance(pub, rospy.Publisher)
        self.assertEqual('std_msgs/Int32', pub.type)

    def test_get_publisher_float(self):
        topic = 'not/a/global/topic'
        topic_type_str = self.topics_and_types[topic]

        pub_map = LanguageToMessageTranslator.get_publisher(
            topic, topic_type_str)

        self.assertIsNotNone(pub_map)
        self.assertEqual(1, len(pub_map))
        self.assertTrue(topic in pub_map)

        pub = pub_map[topic]
        self.assertIsInstance(pub, rospy.Publisher)
        self.assertEqual('std_msgs/Float32', pub.type)

    def test_get_publisher_unknown(self):
        topic = 'unknown_type'
        topic_type_str = self.topics_and_types[topic]

        pub_map = LanguageToMessageTranslator.get_publisher(
            topic, topic_type_str)

        self.assertIsNotNone(pub_map)
        self.assertEqual(0, len(pub_map))

if __name__ == '__main__':
    rostest.rosrun('robot_voice_control', 'test_parse_mapping', TestCase)

__author__ = 'Felix Duvallet'
