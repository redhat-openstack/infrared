import commands


def get_overcloud_nodes():
    exit_code, output = commands.getstatusoutput(
        'source /home/stack/stackrc '
        + '&& openstack server list -f value -c Networks|awk -F\'=\'  \'{print $2}\'')
    return output.split("\n")


def run_cmd_on_overcloud_nodes(cmd, nodes_list):
    output_dict = {}
    for node in nodes_list:
        sshcmd = "ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no heat-admin@{}".format(node)
        status, output = commands.getstatusoutput("{} {}".format(sshcmd, cmd))
        output_dict[node] = output
    return output_dict


def test_check_docker_service_is_running_on_overcloud_nodes():
    print"\t Check that docker service is running on overcloud nodes \n"
    nodes = get_overcloud_nodes()
    result = run_cmd_on_overcloud_nodes("sudo systemctl is-active docker", nodes)
    for node in nodes:
        print "status of docker daemon on node {} : {}".format(node, result[node])
        assert "active" == result[node]


def test_check_docker_containers_running_state_on_overcloud_nodes():
    print "\t Check that docker containers have running state on overcloud nodes \n"
    nodes = get_overcloud_nodes()
    docker_containers_names = run_cmd_on_overcloud_nodes(
        '"sudo docker ps --format \'table {{.Names}}\'|awk \'{if(NR>1)print}\' | sort"',nodes)
    docker_containers = {}
    for node in nodes:
        docker_containers[node] = {key: None for key in docker_containers_names[node].split('\n')}
    for node in nodes:
        for name in docker_containers[node].keys():
            cmd = '"sudo docker ps -f name=%s ' \
                  '--format \'table {{.Status}}\'|awk \'{if(NR>1)print}\' | sort"' % (name)
            docker_containers[node][name] = run_cmd_on_overcloud_nodes(cmd, [node, ])[node]
            print name + ": " + docker_containers[node][name]+"\n"
            assert "Up" in docker_containers[node][name]


def test_check_docker_container_volume():
    print "\t Check that dir for docker containers volumes exist on overcloud nodes \n"
    nodes = get_overcloud_nodes()
    docker_container_volumes = run_cmd_on_overcloud_nodes(
        'sudo ls -l /var/lib/docker/containers', nodes)
    for node in nodes:
        assert "No such file or directory" not in docker_container_volumes[node]


def test_check_openstack_services_in_docker_containers():
    print "\t Check that openstack services running in docker containers on overcloud nodes \n"
    nodes = get_overcloud_nodes()
    docker_containers_process={}
    docker_containers_names = run_cmd_on_overcloud_nodes(
        '"sudo docker ps --format \'table {{.Names}}\'|awk \'{if(NR>1)print}\' | sort"', nodes)
    for node in nodes:
        docker_containers_process[node] = {key: None for key in docker_containers_names[node].split('\n')}
    for node in nodes:
        for name in docker_containers_process[node].keys():
            cmd = 'sudo docker exec %s ps -aux |grep %s|grep -v ps' % (name, name[:4])
            docker_containers_process[node][name] = run_cmd_on_overcloud_nodes(cmd, [node, ])[node]
            print node + "\n" + name + "\n" + docker_containers_process[node][name] + "\n"
            assert len(docker_containers_process[node][name]) != 0



def main():
    test_check_docker_service_is_running_on_overcloud_nodes();
    test_check_docker_containers_running_state_on_overcloud_nodes()
    test_check_docker_container_volume()
    test_check_openstack_services_in_docker_containers()

if __name__ == "__main__":
    main()
