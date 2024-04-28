# It takes a Verilog file, and generates a testbench for it.
import random
import re
import sys


class TestbenchGenerator(object):

    def __init__(self, verilog_file_name=None, output_file_name=None):
        self.verilog_file_name = verilog_file_name
        self.verilog_file = None
        self.output_file_name = output_file_name
        if (output_file_name == None):
            self.output_file = sys.stdout
        self.vcont = ""
        self.mod_name = ""
        self.pin_list = []
        self.clock_name = 'clk'
        self.reset_name = 'rst'

        self.input_pin = []

        if verilog_file_name == None:
            sys.stderr.write("ERROR: You have not specified a input file name.\n")
            sys.exit(1)
        else:
            self.open()
        self.parser()
        self.open_outputfile()

    def open(self, verilog_file_name=None):
        if verilog_file_name != None:
            self.verilog_file_name = verilog_file_name
        try:
            self.verilog_file = open(self.verilog_file_name, 'r')
            self.vcont = self.verilog_file.read()
        except (Exception, e):
            print("ERROR:Open and read file error.\n ERROR:    %s" % e)
            sys.exit(1)

    def open_outputfile(self, output_file_name=None):
        try:
            if (output_file_name == None):
                if (self.output_file_name == None):
                    ofname = "tb_%s.v" % self.mod_name
                    self.output_file = open(ofname, 'w')
                    print("You have not specify a output file name, use '%s' instead." % ofname)
                else:
                    self.output_file = open(self.output_file_name, 'w')
                    print('''------------------ Output file is '%s'. ----------------''' % self.output_file_name)
                    print('''------------------------------------------------------------------''')
            else:
                self.output_file = open(output_file_name, 'w')
                print("Output file is '%s'." % output_file_name)
                print('''------------------------------------------------------------------''')
        except Exception as e:
            print("ERROR:open and write output file error. \n ERROR:    %s" % e)
            sys.exit(1)

    def clean_other(self, text):
        text = re.sub(r"//[^\n^\r]*", '\n', text)
        text = re.sub(r"/\*.*\*/", '', text)
        text = re.sub(r"[^\n^\r]+`[^\n^\r]*", '\n', text)
        text = re.sub(r'    +', ' ', text)
        return text

    def parser(self):
        print("-------------------------- Parsering....-------------------------- ")
        print('''------------------------------------------------------------------''')
        mod_pattern = r"module[\s]+(\S*)[\s]*\([^\)]*\)[\s\S]*"

        module_result = re.findall(mod_pattern, self.clean_other(self.vcont))
        self.mod_name = module_result[0]

        self.parser_inoutput()
        self.find_clk_rst()

    def parser_inoutput(self):
        pin_list = self.clean_other(self.vcont)

        comp_pin_list_pre = []
        for i in re.findall(r'(input|output|inout)[\s]+([^;,\)]+)[\s]*[;,]', pin_list):
            comp_pin_list_pre.append((i[0], re.sub(r"^reg[\s]*", "", i[1])))

        comp_pin_list = []
        type_name = ['reg', 'wire', 'wire', "ERROR"]
        for i in comp_pin_list_pre:
            x = re.split(r']', i[1])
            type = 0;
            if i[0] == 'input':
                type = 0
            elif i[0] == 'output':
                type = 1
            elif i[0] == 'inout':
                type = 2
            else:
                type = 3

            if len(x) == 2:
                x[1] = re.sub('[\s]*', '', x[1])
                comp_pin_list.append((i[0], x[1], x[0] + ']', type_name[type]))
            else:
                comp_pin_list.append((i[0], x[0], '', type_name[type]))

        self.pin_list = comp_pin_list

    def print_dut(self):
        max_len = 0
        for cpin_name in self.pin_list:
            pin_name = cpin_name[1]
            if len(pin_name) > max_len:
                max_len = len(pin_name)

        self.print_to_file("%s uut (\n" % self.mod_name)

        align_cont = self.align_print([("", "." + x[1], "(", x[1], '),') for x in self.pin_list], 4)
        align_cont = align_cont[:-2] + "\n"
        self.print_to_file(align_cont)

        self.print_to_file(");\n")

    def print_wires(self):
        self.print_to_file(self.align_print([(x[3], x[2], x[1], ';') for x in self.pin_list], 4))
        self.print_to_file("\n")

    def print_clock_gen(self):
        fsdb = "    $dumpfile(\"db_tb_%s.vcd\");\n    $dumpvars(0, tb_%s);\n" % (self.mod_name, self.mod_name)

        clock_gen_text = "\nparameter PERIOD = 10;\n\ninitial begin\n%s    CLK = 1'b0;\n    #(PERIOD/2);\n    forever\n        #(PERIOD/2) CLK = ~CLK;\n\n" % fsdb
        self.print_to_file(re.sub('CLK', self.clock_name, clock_gen_text))

    def find_clk_rst(self):
        for pin in self.pin_list:
            if re.match(r'[\S]*(clk|clock)[\S]*', pin[1]):
                self.clock_name = pin[1]
                print("I think your clock signal is '%s'." % pin[1])
                print('''------------------------------------------------------------------''')
                break

        for pin in self.pin_list:
            if re.match(r'rst|reset', pin[1]):
                self.reset_name = pin[1]
                print("I think your reset signal is '%s'." % pin[1])
                print('''------------------------------------------------------------------''')
                break

    def print_testbench(self):
        for pin in self.pin_list:
            input_pin = []
            for pin in self.pin_list:
                if 'input' in pin:
                    if (pin[1] not in input_pin):
                        if not (re.match(r'[\S]*(clk|clock)[\S]*', pin[1])) and not (re.match(r'rst|reset', pin[1])):
                            input_pin.append(pin[1])
        input_no = len(input_pin)
        input = [0, 1]
        delay = 10

        if input_no == 1:
            for i in ["1'b0", "1'b1"]:
                self.print_to_file("\t#{} \n".format(delay))
                delay = delay + 20
                self.print_to_file("\t")
                self.print_to_file("{0} = {1}".format(input_pin[0], i))
                self.print_to_file("\n")

        elif input_no == 2:
            for i in ["1'b0", "1'b1"]:
                for j in ["1'b0", "1'b1"]:
                    self.print_to_file("\t#{} \n".format(delay))
                    delay = delay + 20
                    self.print_to_file("\t")
                    self.print_to_file("{0} = {1}, {2} = {3}".format(input_pin[0], i, input_pin[1], j))
                    self.print_to_file("\n")

        elif input_no == 3:
            for i in ["1'b0", "1'b1"]:
                for j in ["1'b0", "1'b1"]:
                    for k in ["1'b0", "1'b1"]:
                        self.print_to_file("\t#{} \n".format(delay))
                        delay = delay + 20
                        self.print_to_file("\t")
                        self.print_to_file(
                            "{0} = {1}, {2} = {3}, {4} = {5}".format(input_pin[0], i, input_pin[1], j, input_pin[2], k))
                        self.print_to_file("\n")

        elif input_no == 4:
            for i in range(10):
                i = random.choice(input)
                j = random.choice(input)
                k = random.choice(input)
                l = random.choice(input)
                self.print_to_file("\t#{} \n".format(delay))
                delay = delay + 20
                self.print_to_file("\t")
                self.print_to_file(
                    "{0} = 1'b{1}, {2} = 1'b{3}, {4} = 1'b{5}, {6} = 1'b{7}".format(input_pin[0], i, input_pin[1], j,
                                                                                    input_pin[2], k, input_pin[3], l))
                self.print_to_file("\n")

        elif input_no == 5:
            for i in range(10):
                i = random.choice(input)
                j = random.choice(input)
                k = random.choice(input)
                l = random.choice(input)
                m = random.choice(input)
                self.print_to_file("\t#{} \n".format(delay))
                delay = delay + 20
                self.print_to_file("\t")
                self.print_to_file(
                    "{0} = 1'b{1}, {2} = 1'b{3}, {4} = 1'b{5}, {6} = 1'b{7}, {8} = 1'b{9}".format(input_pin[0], i,
                                                                                                  input_pin[1], j,
                                                                                                  input_pin[2], k,
                                                                                                  input_pin[3], l,
                                                                                                  input_pin[4], m))
                self.print_to_file("\n")

        elif input_no == 6:
            for i in range(10):
                i = random.choice(input)
                j = random.choice(input)
                k = random.choice(input)
                l = random.choice(input)
                m = random.choice(input)
                n = random.choice(input)
                self.print_to_file("\t#{} \n".format(delay))
                delay = delay + 20
                self.print_to_file("\t")
                self.print_to_file(
                    "{0} = 1'b{1}, {2} = 1'b{3}, {4} = 1'b{5}, {6} = 1'b{7}, {8} = 1'b{9}, {10} = 1'b{11}".format(
                        input_pin[0], i, input_pin[1], j, input_pin[2], k, input_pin[3], l, input_pin[4], m,
                        input_pin[5], n))
                self.print_to_file("\n")

        elif input_no == 7:
            for i in range(10):
                i = random.choice(input)
                j = random.choice(input)
                k = random.choice(input)
                l = random.choice(input)
                m = random.choice(input)
                n = random.choice(input)
                o = random.choice(input)
                self.print_to_file("\t#{} \n".format(delay))
                delay = delay + 20
                self.print_to_file("\t")
                self.print_to_file(
                    "{0} = 1'b{1}, {2} = 1'b{3}, {4} = 1'b{5}, {6} = 1'b{7}, {8} = 1'b{9}, {10} = 1'b{11}, {12} = 1'b{13}".format(
                        input_pin[0], i, input_pin[1], j, input_pin[2], k, input_pin[3], l, input_pin[4], m,
                        input_pin[5], n, input_pin[6], o))
                self.print_to_file("\n")

        elif input_no == 8:
            for i in range(10):
                i = random.choice(input)
                j = random.choice(input)
                k = random.choice(input)
                l = random.choice(input)
                m = random.choice(input)
                n = random.choice(input)
                o = random.choice(input)
                p = random.choice(input)
                self.print_to_file("\t#{} \n".format(delay))
                delay = delay + 20
                self.print_to_file("\t")
                self.print_to_file(
                    "{0} = 1'b{1}, {2} = 1'b{3}, {4} = 1'b{5}, {6} = 1'b{7}, {8} = 1'b{9}, {10} = 1'b{11}, {12} = 1'b{13}, {14} = 1'b{15}".format(
                        input_pin[0], i, input_pin[1], j, input_pin[2], k, input_pin[3], l, input_pin[4], m,
                        input_pin[5], n, input_pin[6], o, input_pin[7], p))
                self.print_to_file("\n")

        elif input_no == 9:
            for i in range(10):
                i = random.choice(input)
                j = random.choice(input)
                k = random.choice(input)
                l = random.choice(input)
                m = random.choice(input)
                n = random.choice(input)
                o = random.choice(input)
                p = random.choice(input)
                q = random.choice(input)
                self.print_to_file("\t#{} \n".format(delay))
                delay = delay + 20
                self.print_to_file("\t")
                self.print_to_file(
                    "{0} = 1'b{1}, {2} = 1'b{3}, {4} = 1'b{5}, {6} = 1'b{7}, {8} = 1'b{9}, {10} = 1'b{11}, {12} = 1'b{13}, {14} = 1'b{15}, {16} = 1'b{17}".format(
                        input_pin[0], i, input_pin[1], j, input_pin[2], k, input_pin[3], l, input_pin[4], m,
                        input_pin[5], n, input_pin[6], o, input_pin[7], p, input_pin[8], q))
                self.print_to_file("\n")

        self.print_to_file("\nend\n")

    def print_module_head(self):
        self.print_to_file("`include \"timescale.v\"\nmodule tb_%s;\n\n" % self.mod_name)

    def print_module_end(self):
        self.print_to_file("endmodule\n")

    def print_to_file(self, text):
        self.output_file.write(text)

    def close(self):
        if self.verilog_file != None:
            self.verilog_file.close()
        print('''------------------------ Output finished. ------------------------''')
        print('''------------------------------------------------------------------''')

    def align_print(self, content, indent):
        row_len = len(content)
        col_len = len(content[0])
        align_cont = [""] * row_len
        for i in range(col_len):
            col = [x[i] for x in content]
            max_len = max(list(map(len, col)))
            for i in range(row_len):
                l = len(col[i])
                align_cont[i] += "%s%s" % (col[i], (indent + max_len - l) * ' ')

        align_cont = [re.sub('[ ]*$', '', s) for s in align_cont]
        return "\n".join(align_cont) + "\n"

    def comment(self):
        self.print_to_file(
            "/* \nThis is the Auto-Generated testbench. \nWritten by Darshil Mavadiya and Anant Kothivar \n*/\n\n")


if __name__ == "__main__":

    print('''------------------------------------------------------------------''')
    print('''-------------------- Generating the testbench.--------------------''')
    print('''------------------------------------------------------------------''')

    output_file_name = None

    if len(sys.argv) == 1:
        sys.stderr.write("ERROR: You have not specified a input file name.\n")
        print('''------------------------------------------------------------------''')
        print("HOW TO USE: testbench-generator input_verilog_file_name [output_testbench_file_name]")
        print('''------------------------------------------------------------------''')
        sys.exit(1)
    elif len(sys.argv) == 3:
        output_file_name = sys.argv[2]

    tbgen = TestbenchGenerator(sys.argv[1], output_file_name)

    tbgen.comment()
    tbgen.print_module_head()
    tbgen.print_wires()
    tbgen.print_dut()
    tbgen.print_clock_gen()
    tbgen.print_testbench()
    tbgen.print_module_end()

    tbgen.close()
