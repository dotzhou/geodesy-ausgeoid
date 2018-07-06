#!/usr/bin/env bash

set -e

script="$(basename "${BASH_SOURCE[0]}")"


################################################################################
function usage {
    cat <<USAGE

Usage:      ${script} [-options]

where options include:
    -h      print this help message

    mandatory options:

    -f      fullpath for rinex data file
    -e      environment
    -k      token from OpenAM

USAGE

  exit 0
}



################################################################################
function validate {

    if [[ -z $rinex_file ]]; then
        usage
    fi

    if [[ -z $environment ]]; then
        usage
    fi

    if [[ -z $open_am_token ]]; then
        usage
    fi
}



################################################################################
function upload {

    case "$environment" in
        ( dev )
            openam_auth_url=https://devgeodesy-openam.geodesy.ga.gov.au/openam/oauth2
            aws_api_gateway_url=https://api.dev-archive.geodesy.ga.gov.au
            ;;
        ( test )
            openam_auth_url=https://testgeodesy-openam.geodesy.ga.gov.au/openam/oauth2
            aws_api_gateway_url=https://api.test-archive.geodesy.ga.gov.au
            ;;
        ( prod )
            openam_auth_url=https://prodgeodesy-openam.geodesy.ga.gov.au/openam/oauth2
            aws_api_gateway_url=https://api.archive.geodesy.ga.gov.au
            ;;
    esac

# Provide test credentials below
    if [[ $environment == "test" ]]; then
        clientId=
        clientPassword=
        username=
        password=
    elif [[ $environment == "prod" ]]; then
        clientId=
        clientPassword=""
        username=
        password=
    else
        echo "Not implemented yet!"
        exit 1;
    fi

    if [ -s "$rinex_file" ]; then
        curl --insecure -i -XPUT -H "Content-type: application/octet-stream" \
             --data-binary @"${rinex_file}" ${aws_api_gateway_url}/submit/"$(basename "$rinex_file")" -H "Authorization: Bearer ${open_am_token}"
    else
        exit -1;
    fi
}


if [[ $# -eq 0 ]]; then
    usage
fi


################################################################################
while getopts ":h :f: :e: :k:" opt; do
    case $opt in
        (h)
            usage
            ;;
        (e)
            environment=$OPTARG
            if [[ ${environment} != "dev" && ${environment} != "test" && ${environment} != "prod" ]]; then
                usage
            fi
            ;;
        (f)
            rinex_file=$OPTARG
            ;;
        (k)
            open_am_token=$OPTARG
            ;;
        (\?)
            echo "" >&2
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        (:)
            echo "" >&2
            echo "Option -$OPTARG requires an argument" >&2
            usage
            ;;
    esac
done

validate

upload

exit 0

