SCOPE BEGIN
  foo =>
    VAR BEGIN
      type:
        RECORD BEGIN
          SCOPE BEGIN
            b =>
              VAR BEGIN
                type:
                  INTEGER
              END VAR
            int =>
              VAR BEGIN
                type:
                  INTEGER
              END VAR
          END SCOPE
        END RECORD
    END VAR
  int =>
    INTEGER
END SCOPE
