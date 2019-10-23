from waitress import serve
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest
from subprocess import Popen, PIPE
from fuzz_response import FuzzResponse, RunResult, VMResult
import uuid
import shutil
import os

VM_DICT = {'spec-interpreter': './interpreter/wasm'}


def run_command(command):
    process = Popen(command.split(' '), stdout=PIPE, stderr=PIPE)
    process.wait()
    return process.returncode, process.stdout.read().decode(), process.stderr.read().decode()


def run_mutation(file_path):
    mutation_path = file_path + '-new.wast'
    ret_code, _, _ = run_command('./interpreter/wasm %s -o %s' % (file_path, mutation_path))
    if ret_code != 0:
        return None
    return mutation_path


def evaluate_wasm(vm_path, file_path):
    return RunResult(*run_command(vm_path + ' ' + file_path))


def evaluate_all_vms(origin_path, mutation_path):
    run_results = {}

    for vm_name, vm_path in VM_DICT.items():
        run_results[vm_name] = VMResult(evaluate_wasm(vm_path, origin_path), evaluate_wasm(vm_path, mutation_path))

    return run_results


def render_static(request):
    static_file = request.matchdict['static_file']
    if static_file == '':
        static_file = 'index.html'
    with open('./public/' + static_file, 'rb') as file:
        return Response(file.read())


def upload_file(request):
    input_file = request.POST['file'].file
    save_path = os.path.abspath('./tmp/%s.wast' % uuid.uuid4())

    input_file.seek(0)
    with open(save_path, 'wb+') as output_file:
        shutil.copyfileobj(input_file, output_file)

    mutation_path = run_mutation(save_path)
    if mutation_path is None:
        return HTTPBadRequest('Mutation Failed')

    with open(save_path, 'rb') as origin_file, open(mutation_path, 'rb') as mutation_file:
        fuzz_response = FuzzResponse(origin_file.read().decode(), mutation_file.read().decode(),
                                     evaluate_all_vms(save_path, mutation_path))
        return Response(fuzz_response.to_json())


if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('upload', '/upload')
        config.add_view(upload_file, route_name='upload')
        config.add_route('home', '/{static_file:.*}')
        config.add_view(render_static, route_name='home')
        app = config.make_wsgi_app()
    serve(app, host='0.0.0.0', port=6543)
