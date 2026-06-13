# Wraps the repo-level platform-independent flight core as an IDF component.
set(FC_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../fc_core)

idf_component_register(
    SRCS
        ${FC_DIR}/src/fc_core.c
        ${FC_DIR}/src/fc_estimator.c
        ${FC_DIR}/src/fc_control.c
        ${FC_DIR}/src/fc_commander.c
        ${FC_DIR}/src/fc_pid.c
        ${FC_DIR}/src/fc_params.c
        ${FC_DIR}/src/fc_sdk.c
    INCLUDE_DIRS ${FC_DIR}/include
    PRIV_INCLUDE_DIRS ${FC_DIR}/src
)
