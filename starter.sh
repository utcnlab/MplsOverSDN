#!/bin/bash

if [[ $1 == "--help" ]] || [[ $1 == "help" ]]
then
    echo Requires Python 2.7 and pip
    echo Commands:
    echo -e ./starter.sh help '\n\t' Show this page
    echo -e ./starter.sh install '\n\t' Install Mininet and Packages
    echo -e ./starter.sh '\n\t' Start Controller and Mininet with Simple Topology without loop and will show it
    echo -e ./starter.sh loop '\n\t' Start Controller and Mininet with Simple Topology with loop and will show it
    echo -e ./starter.sh loop noview '\n\t' Start Controller and Mininet with Simple Topology with loop
    echo -e ./starter.sh ./topologies/simpleNet.json '\n\t' Start Controller and Mininet Based on simpleNet.json file
    echo -e ./starter.sh ./topologies/simpleNetWithLoop.json '\n\t' Start Controller and Mininet Based on simpleNetWithLoop.json file
    echo -e ./starter.sh './topologies/*.json' noview '\n\t' Start Controller and Mininet Based on *.json and "won't" show topology
    exit 0
fi

topology=${1:-simpleNet.json}

if [[ $1 == "loop" ]]
then
    topology=simpleNetWithLoop.json
fi

cmds1="sh ./scripts/runController.sh ${topology}"

cmds2="sh ./scripts/runMininet.sh ${topology}"

cmds3="sh ./scripts/runViewer.sh ${topology}"

cmds4="sh ./scripts/runDevInstaller.sh"

cmds5="sh ./scripts/runCleaner.sh"

if [[ $1 == "install" ]]
then
    echo -------------------- ${cmds4} --------------------
    ${cmds4}
    exit 0
fi

echo -------------------- ${cmds5} --------------------
${cmds5}
sleep 1


echo -------------------- ${cmds1} --------------------
gnome-terminal -- ${cmds1}
sleep 1


echo -------------------- ${cmds2} --------------------
gnome-terminal -- ${cmds2}


if [[ $2 == "noview" ]] || [[ $3 == "noview" ]]
then
    exit 0
fi

echo -------------------- ${cmds3} --------------------
gnome-terminal -- ${cmds3}
exit 0
