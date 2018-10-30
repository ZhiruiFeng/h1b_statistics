import sys
from collections import Counter, defaultdict

class H1bAnalysor(object):

    def __init__(self, data_source, verbose=False):
        self.data_source = data_source
        self.occupations = Counter()
        self.states = Counter()
        self.top10_occ = []
        self.top10_states = []

        # mapping the code and name in occupation
        self.soc_map = defaultdict()

        # Valiables to get the value of specific colums
        self.columns = 0
        self.CASE_STATUS = -1
        self.WORKSITE_STATE = -1
        self.SOC_CODE = -1
        self.SOC_NAME = -1

        # Count the number of all certified
        self.cnt = 0

        self.verbose = verbose
        self._get_index()

    def _get_index(self):
        '''Here we just make it being able to handle the 2014-2016 data format automately'''
        line = self.data_source.readline()
        content = line.strip().split(';')
        self.columns = len(content)
        for i, v in enumerate(content):
            if v == 'CASE_STATUS' or v == 'STATUS':
                self.CASE_STATUS = i
            elif v == 'WORKSITE_STATE' or v == 'LCA_CASE_WORKLOC1_STATE':
                self.WORKSITE_STATE = i
            elif v == 'SOC_CODE' or v == 'LCA_CASE_SOC_CODE':
                self.SOC_CODE = i
            elif v == 'SOC_NAME' or v == 'LCA_CASE_SOC_NAME':
                self.SOC_NAME = i

    def set_index(self, total_column, case_status, worksite_state, soc_code, soc_name):
        '''For new form of file, we set which column to get which information'''
        self.columns = total_column
        self.CASE_STATUS = case_status
        self.WORKSITE_STATE = worksite_state
        self.SOC_CODE = soc_code
        self.SOC_NAME = soc_name

    def analysis(self):
        line = self.data_source.readline()
        self.cnt = 0
        tmp = 0
        temcounter = Counter()
        if self.verbose:
            print("Some sample of invalid rows")
        while line:
            line = line.strip()
            content = self._split_line(line)
            id = content[0]
            if self.verbose and len(id) > 0 and int(id)%10000==0:
                print("Records processed {}".format(id))
            if self.verbose and len(content) != self.columns:
                if temcounter[len(content)] <= 5:
                    print(self.columns, len(content), line)
                temcounter[len(content)]+=1
                tmp += 1
                line = self.data_source.readline()
                continue

            case_status = content[self.CASE_STATUS]
            worksite_state = content[self.WORKSITE_STATE]
            soc_code = content[self.SOC_CODE]
            soc_name = content[self.SOC_NAME]

            # Count but don't get extract state and job title
            if not case_status or not worksite_state or not soc_code or not soc_name:
                self.cnt += 1
                line = self.data_source.readline()
                continue

            soc_code = self._validate_soc_code(soc_code, soc_name)
            if not soc_code:
                self.cnt += 1
                line = self.data_source.readline()
                continue

            if case_status == 'CERTIFIED':
                self.cnt += 1
                self.occupations[soc_code] += 1
                self.states[worksite_state] += 1
            line = self.data_source.readline()
        if self.verbose:
            print("Number of invalid rows:{}".format(tmp))

    def _split_line(self, string):
        '''Some value of colums may includs ';', thus we rewrite the split function'''
        double_quate, left, right, l = 0, 0, 0, len(string)
        out = []
        while right <= l:
            if right == l or (string[right] == ';' and not double_quate):
                if left < right:
                    out.append(string[left:right].strip())
                else:
                    out.append('')
                left = right + 1
            elif string[right] == '\"':
                double_quate = 1 - double_quate
            right += 1
        return out

    def _validate_soc_code(self, soc_code, soc_name):
        code = soc_code.strip().split('.')[0]  # Some like '10-1021.00'
        if len(code) == 7 and code[2] == '-': # Valid code'10-1021'
            pass
        elif len(code) == 6 and code[2] != '-': # '101021' Can infer the right code
            code = code[:2]+'-'+code[2:]
        else:  # Could not infer the right code
            code = ''

        # Make the soc_name more formal, without \" at two ends
        soc_name = soc_name.strip()
        while len(soc_name) > 1 and soc_name[0]=='"' and soc_name[-1] == '"':
            soc_name = soc_name[1:-1].strip()

        if code and (code not in self.soc_map):
            self.soc_map[code] = soc_name
        return code

    def _get_top10_states(self, size):
        self.top10_states = []
        windows = []
        for des, cnt in self.states.items():
            if len(windows) < size:
                windows.append((-cnt, des))
            else:
                maxv = max(windows)
                if (-cnt, des) < maxv:
                    index = windows.index(maxv)
                    windows[index] = (-cnt, des)
        windows.sort()
        for cnt, des in windows:
            self.top10_states.append((des, -cnt))

    def _get_top10_occ(self, size):
        self.top10_occ = []
        windows = []
        for code, cnt in self.occupations.items():
            des = self.soc_map[code]
            if len(windows) < size:
                windows.append((-cnt, des))
            else:
                maxv = max(windows)
                if (-cnt, des) < maxv:
                    index = windows.index(maxv)
                    windows[index] = (-cnt, des)
        windows.sort()
        for cnt, des in windows:
            self.top10_occ.append((des, -cnt))

    def get_occupations_result(self, out_file, size):
        out_file.write("TOP_OCCUPATIONS;NUMBER_CERTIFIED_APPLICATIONS;PERCENTAGE\n")
        self._get_top10_occ(size)
        for des, cnt in self.top10_occ:
            percent = (float(cnt)/float(self.cnt))*100
            out_file.write('{};{};{}%\n'.format(des, cnt, percent))

    def get_states_result(self, out_file, size):
        out_file.write("TOP_STATES;NUMBER_CERTIFIED_APPLICATIONS;PERCENTAGE\n")
        self._get_top10_states(size)
        for des, cnt in self.top10_states:
            percent = (float(cnt)/float(self.cnt))*100
            out_file.write('{};{};{}%\n'.format(des, cnt, percent))


if __name__ == "__main__":
    # Read Parameters About Input and Output
    args = sys.argv[1:]
    if len(args) != 3:
        exit("Please give 1 Input file and 2 Output file.")

    in_data = args[0]
    out_occupations = args[1]
    out_states = args[2]

    TOP_NUMBER = 10
    Verbose = False  # Could set true to get more runtime output
    with open(in_data, 'r') as source:
        analysor = H1bAnalysor(source, Verbose)
        analysor.analysis()
        outfile_occ = open(out_occupations, 'w')
        analysor.get_occupations_result(outfile_occ, TOP_NUMBER)
        outfile_state = open(out_states, 'w')
        analysor.get_states_result(outfile_state, TOP_NUMBER)
        outfile_occ.close()
        outfile_state.close()
