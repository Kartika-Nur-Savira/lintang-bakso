"""
Helper to execute notebook cells in Python, capture stdout/stderr and matplotlib figures,
and produce fully executed .ipynb notebooks with embedded rich outputs.
"""

import io
import os
import sys
import base64
import contextlib
import nbformat as nbf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class NotebookRunner:
    def __init__(self, working_dir='notebooks'):
        self.working_dir = working_dir
        self.global_env = {}
        # Menambahkan parent dir ke sys.path
        abs_parent = os.path.abspath(os.path.join(working_dir, '..'))
        if abs_parent not in sys.path:
            sys.path.insert(0, abs_parent)
        self.global_env['__name__'] = '__main__'
        self.global_env['sys'] = sys
        
    def run_notebook(self, nb: nbf.NotebookNode, output_path: str):
        # Berpindah ke working dir sementara saat eksekusi
        cwd = os.getcwd()
        os.makedirs(self.working_dir, exist_ok=True)
        os.chdir(self.working_dir)
        
        execution_count = 1
        try:
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    cell.execution_count = execution_count
                    cell.outputs = []
                    
                    stdout_capture = io.StringIO()
                    stderr_capture = io.StringIO()
                    
                    # Bersihkan figure matplotlib sebelum run
                    plt.close('all')
                    
                    with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                        try:
                            # Kompilasi dan eksekusi
                            code = cell.source
                            exec(code, self.global_env)
                        except Exception as e:
                            import traceback
                            tb_str = traceback.format_exc()
                            print(tb_str, file=sys.stderr)
                            
                    out_text = stdout_capture.getvalue()
                    err_text = stderr_capture.getvalue()
                    
                    if out_text:
                        cell.outputs.append(nbf.v4.new_output(
                            output_type='stream',
                            name='stdout',
                            text=out_text
                        ))
                    if err_text:
                        cell.outputs.append(nbf.v4.new_output(
                            output_type='stream',
                            name='stderr',
                            text=err_text
                        ))
                        
                    # Tangkap active matplotlib figures jika ada
                    figs = [plt.figure(i) for i in plt.get_fignums()]
                    for fig in figs:
                        img_buf = io.BytesIO()
                        fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=130)
                        img_buf.seek(0)
                        img_b64 = base64.b64encode(img_buf.read()).decode('utf-8')
                        cell.outputs.append(nbf.v4.new_output(
                            output_type='display_data',
                            data={'image/png': img_b64, 'text/plain': '<Figure size ...>'},
                            metadata={}
                        ))
                    plt.close('all')
                    execution_count += 1
        finally:
            os.chdir(cwd)
            
        with open(output_path, 'w') as f:
            nbf.write(nb, f)
        print(f"Executed notebook saved successfully to {output_path}")
