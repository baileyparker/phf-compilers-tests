SCOPE BEGIN
  kerfuffle =>
    VAR BEGIN
      type:
        INTEGER
    END VAR
  shadowScope =>
    VAR BEGIN
      type:
        RECORD BEGIN
          SCOPE BEGIN
            kerfuffle =>
              VAR BEGIN
                type:
                  ARRAY BEGIN
                    type:
                      INTEGER
                    length:
                      22
                  END ARRAY
              END VAR
          END SCOPE
        END RECORD
    END VAR
END SCOPE
