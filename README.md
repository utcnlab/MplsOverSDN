# MPLS over SDN

Bachelor of Science, Information Technology, *Computer Network Laboratory*, **University of Tehran**

Implementing **MPLS** (Multi Protocol Label Switch) Algorithm Over **SDN** (Software Defined Network)

Leading Teacher: Prof. Khunsari

I'm everywhere :)


## Manual

You can use starter.sh script to easily start scenarios and install required dependencies. Take below stepes to setup your environments.

1. Make starter.sh executable by `chmod +x starter.sh`

2. Install Mininet and Packages `./starter.sh install`

3. Below table lists diffrent job that starter.sh script can do.

| argument                            | action                                                                          |
| ----------------------------------- |---------------------------------------------------------------------------------|
| help                                | Show help                                                                       |
| install                             | Install Mininet and Packages                                                    |
| -                                   | Start Controller and Mininet with Simple Topology without loop and will show it |
| loop                                | Start Controller and Mininet with Simple Topology with loop and will show it    |
| loop noview                         | Start Controller and Mininet with Simple Topology with loop                     |
| ./topologies/simpleNet.json         | Start Controller and Mininet Based on simpleNet.json file                       |
| ./topologies/simpleNetWithLoop.json | Start Controller and Mininet Based on simpleNetWithLoop.json file               |
| ./topologies/*.json noview          | Start Controller and Mininet Based on *.json and won't show topology            |
