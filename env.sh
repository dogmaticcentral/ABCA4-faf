# source this to add the path to PYTHONPATH
myname=${BASH_SOURCE[0]}
fullpath=$(realpath  "$myname")  # get the full path to us
mydir=$(dirname "$fullpath")  # directory only

if [ -z $PYTHONPATH ]
then
      # if PYTHONPATH not set yet, than it's mydir
      export PYTHONPATH=$mydir/src
else
      # delete all appearance of :$mydir from the existing path
      PYTHONPATH=${PYTHONPATH//:$mydir/}
      #  if $mydir already first in the PYTHONPATH do nothing
      if [[ $PYTHONPATH == "$mydir" || $PYTHONPATH =~ "$mydir:".* ]]
      then # do nothing
          :
      else # prepend :$mydir from the existing path
          export PYTHONPATH=$mydir:$PYTHONPATH/src
      fi
fi
echo PYTHONPATH is  set to $PYTHONPATH

export PREFECT_API_URL=http://127.0.0.1:4200/api
