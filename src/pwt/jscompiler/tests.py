import unittest
from cStringIO import StringIO

import soy_wsgi

import jinja2.compiler
import jinja2.nodes
import jinja2.optimizer
import jinja2.runtime

import jscompiler


def generateMacro(node, environment, name, filename, stream):
    generator = jscompiler.MacroCodeGenerator(environment, None, None, stream)
    eval_ctx = jinja2.nodes.EvalContext(environment, name)
    eval_ctx.namespace = "test"
    generator.blockvisit(node.body, jscompiler.JSFrame(eval_ctx))


class JSCompilerTemplateTestCase(unittest.TestCase):

    def setUp(self):
        super(JSCompilerTemplateTestCase, self).setUp()

        self.loader = jinja2.PackageLoader("pwt.jscompiler", "test_templates")
        self.env = jinja2.Environment(
            loader = self.loader,
            extensions = ["pwt.jscompiler.jscompiler.Namespace"],
            )

    def get_compile_from_string(self, source, name = None, filename = None):
        node = self.env._parse(source, name, filename)
        # node = jinja2.optimizer.optimize(node, self.env)

        return node

    def get_compile(self, name):
        # load
        source, filename, uptodate = self.loader.get_source(self.env, name)
        # code = env.compile(source, name, filename)

        return self.get_compile_from_string(source, name, filename)

    def test_missing_namespace1(self):
        node = self.get_compile("missing_namespace.html")
        stream = StringIO()
        self.assertRaises(jinja2.compiler.TemplateAssertionError, jscompiler.generate, node, self.env, "", "", stream = stream)

    def test_const1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
Hello, world!
{% endmacro %}""")
        stream = StringIO()
        generateMacro(
            node, self.env, "const.html", "const.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
{{ name }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var1.html", "var1.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', opt_data.name, '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var2(self):
        node = self.get_compile_from_string("""{% macro helloName() %}
Hello, {{ name }}!
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.helloName = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_for1(self):
        # XXX - test recursive loop
        node = self.get_compile_from_string("""{% macro fortest() %}
{% for item in data %}
  Item {{ item }}.
{% else %}
  No items.
{% endfor %}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    if (itemListLen > 0) {
        for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
            var itemData = itemList[itemIndex];
            output.append('\\n  Item ', itemData, '.\\n');
        }
    } else {
        output.append('\\n  No items.\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_for2(self):
        # test loop.index0 variables
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest() %}{% for item in data %}{{ loop.index0 }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');
xxx.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for3(self):
        # test loop.index variables
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest() %}{% for item in data %}{{ loop.index }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');
xxx.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for4(self):
        # test loop.revindex & loop.revindex0 variables
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest() %}{% for item in data %}{{ loop.revindex }} - {{loop.revindex0 }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');
xxx.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemListLen - itemIndex - 1, ' - ', itemListLen - itemIndex);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for5(self):
        # test loop.length & loop.first & loop.last variables
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest() %}{% for item in data %}{{ loop.length }} - {{loop.first }} - {{ loop.last }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');
xxx.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemListLen, ' - ', itemIndex == 0, ' - ', itemIndex == (itemListLen - 1));
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for6(self):
        # test invalid loop access
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest() %}{% for item in data %}{{ loop.missing }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        self.assertRaises(
            AttributeError,
            jscompiler.generate,
            node, self.env, "for.html", "for.html", stream = stream)

    def test_for7(self):
        # test loop.index with other variable.
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest() %}{% for item in data %}{{ loop.index }} - {{ name }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');
xxx.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1, ' - ', opt_data.name);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for8(self):
        # test loop.index with other variable, with attribute
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest() %}{% for item in data %}{{ loop.index }} - {{ param.name }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');
xxx.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1, ' - ', opt_data.param && opt_data.param.name);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_if1(self):
        node = self.get_compile_from_string("""{% macro iftest() %}
{% if option %}
Option set.
{% else %}
No option.
{% endif %}
{% endmacro %}
""")

        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.iftest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    if (opt_data.option) {
        output.append('\\nOption set.\\n');
    } else {
        output.append('\\nNo option.\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_if2(self):
        node = self.get_compile_from_string("{% namespace xxx %}{% macro testif() %}{% if option %}{{ option }}{% endif %}{% endmacro %}")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');
xxx.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro1(self):
        node = self.get_compile_from_string("""{% namespace xxx %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}{{ xxx.testif() }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');


xxx.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.testif({}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro2(self):
        # multiple name namespace
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}{{ xxx.ns1.testif() }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');


xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.testif({}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro3(self):
        # call with parament set
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}{{ xxx.ns1.testif(option = true) }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');


xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.testif({option: true}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro4(self):
        # call with parament set, and extra output
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}Hello, {{ xxx.ns1.testif(option = true) }}!{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');


xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('Hello, ');
    xxx.ns1.testif({option: true}, output);
    output.append('!');
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro5(self):
        # call with variable arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}Hello, {{ xxx.ns1.testif(true) }}!{% endmacro %}""")

        stream = StringIO()
        self.assertRaises(jinja2.compiler.TemplateAssertionError,
                          jscompiler.generate,
                          node, self.env, "", "", stream = stream)

    def test_call_macro6(self):
        # call with keywrod arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}Hello, {{ xxx.ns1.testif(**{option: true}) }}!{% endmacro %}""")

        stream = StringIO()
        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generate, node, self.env, "", "", stream = stream)


class JSCompilerTemplateTestCaseOptimized(JSCompilerTemplateTestCase):

    def get_compile(self, name, env = None):
        env = env or self.env
        # load
        source, filename, uptodate = self.loader.get_source(env, name)
        # code = env.compile(source, name, filename)

        node = env._parse(source, name, filename)
        node = jinja2.optimizer.optimize(node, env)

        return node


import webtest

class SoyServer(unittest.TestCase):

    def get_app(self):
        return webtest.TestApp(
            soy_wsgi.Resources(
                url = "/soy/", packages = "pwt.jscompiler:test_templates"))

    def test_soy1(self):
        app = self.get_app()
        self.assertRaises(webtest.AppError, app.get, "/soy/missing.soy")

    def test_soy2(self):
        app = self.get_app()
        res = app.get("/soy/example.soy")