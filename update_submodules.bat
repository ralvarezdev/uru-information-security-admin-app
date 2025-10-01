@echo off

@echo Updating git submodules...
git submodule update --init --recursive --remote
@echo Git submodules updated.