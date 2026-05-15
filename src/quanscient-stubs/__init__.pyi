"""Quanscient Allsolve scripting main module"""

from __future__ import annotations
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    overload,
)
from collections.abc import Sequence

class densemat:
    @overload
    def __init__(self) -> None:
        """
        The `densemat` object stores a row-major array of doubles that corresponds to a dense matrix.
        For storing an array of integers, see `indexmat` object.

        Examples
        --------
        There are several ways of instantiating a `densemat` object. They are listed below:

        **Example 1**: `densemat(numberofrows:int, numberofcolumns:int)`
        The following creates a matrix with 2 rows and 3 columns. The entries may be undefined.
        >>> B = densemat(2,3)

        **Example 2**: `densemat(numberofrows:int, numberofcolumns:int, initvalue:double)`
        This creates a matrix with 2 rows and 3 columns. All entries are assigned the value `initvalue`.
        >>> B = densemat(2,3, 12)
        >>> B.print()
        Matrix size is 2x3
        12 12 12
        12 12 12

        **Example 3**: `densemat(numberofrows:int, numberofcolumns:int, valvec:List[double])`
        This creates a matrix with 2 rows and 3 columns. The entries are assigned the values of `valvec`.
        The length of `valvec` is expected to be equal to the total count of entries in the matrix. So for creating
        a matrix of size $2 \\times 3$, length of `valvec` must be 6.
        >>> B = densemat(2,3, [1,2,3,4,5,6])
        >>> B.print()
        Matrix size is 2x3
        1 2 3
        4 5 6

        **Example 4**: `densemat(numberofrows:int, numberofcolumns:int, init:double, step:double)`
        This creates a matrix with 2 rows and 3 columns. The first entry is assigned the value `init` and the consecutive entries
        are assigned values that increase by steps of `step`.
        >>> B = densemat(2,3, 0, 1)
        >>> B.print()
        Matrix size is 2x3
        0 1 2
        3 4 5

        **Example 5**: `densemat(input:List[densemat])`
        This creates a matrix that is the vertical concatenation of `input` matrices. Since, the concatenation occurs vertically,
        the number of columns in all the input matrices must match.
        >>> A = densemat(2,3, 0)
        >>> B = densemat(1,3, 2)
        >>> AB = densemat([A,B])
        >>> AB.print()
        Matrix size is 3x3
        0 0 0
        0 0 0
        2 2 2
        """

    @overload
    def __init__(self, numberofrows: int, numberofcolumns: int) -> None: ...
    @overload
    def __init__(
        self, numberofrows: int, numberofcolumns: int, initvalue: float
    ) -> None: ...
    @overload
    def __init__(
        self, numberofrows: int, numberofcolumns: int, valvec: Sequence[float]
    ) -> None: ...
    @overload
    def __init__(
        self, numberofrows: int, numberofcolumns: int, init: float, step: float
    ) -> None: ...
    @overload
    def __init__(self, input: Sequence[densemat]) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    def count(self) -> int:
        """
        This counts and returns the total number of entries in the dense matrix.
        $$
        count = (number \\ of \\ rows) \\times (number \\ of \\ columns)
        $$

        Example
        -------
        >>> B = densemat(2,3)
        >>> B.count()
        6
        """
        ...

    def countcolumns(self) -> int:
        """
        This counts and returns the number of columns in the dense matrix.

        Example
        -------
        >>> B = densemat(2,3)
        >>> B.countcolumns()
        3
        """
        ...

    def countrows(self) -> int:
        """
        This counts and returns the number of rows in the dense matrix.

        Example
        -------
        >>> B = densemat(2,3)
        >>> B.countrows()
        2
        """
        ...

    def getvalue(self, rownumber: int, columnnumber: int) -> float: ...
    def print(self) -> None:
        """
        This prints the entries of the dense matrix.

        Example
        -------
        >>> B = densemat(2,3, 0,1)
        >>> B.print()
        Matrix size is 2x3
        0 1 2
        3 4 5
        """
        ...

    def printsize(self) -> None:
        """
        This prints the size of the dense matrix.

        Example
        -------
        >>> B = densemat(2,3)
        >>> B.printsize()
        Matrix size is 2x3
        """
        ...

    def setvalue(self, rownumber: int, columnnumber: int, val: float) -> None: ...
    ...

class eigenvalue:
    @overload
    def __init__(self, form: formulation) -> None:
        """
        The eigenvalue object allows us to solve classical, generalized and polynomial eigenvalue problems. The computation is done by
        SLEPc, a scalable library for eigenvalue problem computation.

        Examples
        --------
        **Example 1:** `eigenvalue(A: mat)`

        This defines a classical eigenvalue problem:
        $$
        Ax = \\lambda x
        $$

        **Example2.1:** `eigenvalue(A:mat, B:mat)`

        This defines a generalized eigenvalue problem  $Ax = \\lambda Bx$.
        Undamped mechanical resonance modes and resonance frequencies can be calculated with this since an **undamped mechanical
        problem** can be written in the form
        $$
        M\\ddot{x} + Kx = 0
        $$
        which for a harmonic excitation at angular frequency $\\omega$ can be rewritten as
        $$
        Kx = {\\omega}^{2}Mx
        $$
        so that the generalized eigen value $\\lambda$ is equal to ${\\omega}^2$.
        To visualize the resonance frequencies of all calculated undamped modes the method `eigenvalue.printeigenfrequencies`
        can be called.

        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Direct eigen solver (works only for non-DDM simulation)
        >>> elasticity.generate()
        >>> eig = eigenvalue(elasticity.K(), elasticity.M())
        >>> eig.compute(5, 0)
        >>>
        >>> eig.printeigenfrequencies()
        >>>
        >>> eigenvalue_real = eig.geteigenvaluerealpart()
        >>> eigenvalue_imag = eig.geteigenvalueimaginarypart()
        >>>
        >>> eigenvector_real = eig.geteigenvectorrealpart()
        >>> eigenvector_imag = eig.geteigenvectorimaginarypart()


        **Example2.2:** `eigenvalue(form: formulation)`

        This is same as the example 2.1 but the eigen solution is obtained iteratively. This can be used for both
        non-DDM and DDM simulation case setup.

        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcompute(1e-6, 1000, 5, 0)
        >>>
        >>> eig.printeigenfrequencies()
        >>>
        >>> eigenvalue_real = eig.geteigenvaluerealpart()
        >>> eigenvalue_imag = eig.geteigenvalueimaginarypart()
        >>>
        >>> eigenvector_real = eig.geteigenvectorrealpart()
        >>> eigenvector_imag = eig.geteigenvectorimaginarypart()


        **Example 3:** `eigenvalue(K: mat, C:mat, M:mat)`

        This defined a second-order polynomial eigenvalue problem $(M\\lambda^2 + C\\lambda + K)x = 0$ which allows getting the
        resonance modes and resonance frequencies for **damped mechanical problems**. The input arguments are respectively the
        mechanical stiffness, damping matrix and mass matrix.
        A second-order polynomial eigenvalue problem attempts to find a solution of the form
        $$
        x(t) = ue^{\\lambda t}, \\lambda = \\alpha + i\\beta = -\\zeta\\omega - i\\omega \\sqrt{1-\\zeta^2}
        $$

        which corresponds to a damped oscillation at frequency $f_{damped} = \\frac{\\beta}{2\\pi}$ with a damping ratio
        $$
        \\zeta = \\frac{-\\alpha}{\\sqrt{(\\alpha^2 + \\beta^2)}}
        $$

        In the case of proportional damping (if and only if $KM^{-1}C$ is symmetric) the oscillation of the undamped system is at
        $\\omega$. The undamped oscillation frequency can then be calculated as
        $$
        f_{undamped} = \\frac{\\sqrt{(\\alpha^2 + \\beta^2)}}{2\\pi}
        $$

        To visualize all relevant resonance information for the computed eigenvalues the method `eigenvalue.printeigenfrequencies`
        can be called.

        **Example 4:** `eigenvalue(inmats: List[mat])`

        This defines an arbitraray order polynomial eigenvalue problem.
        $$
        (inmats[0] + inmats[1]\\lambda + inmats[2]\\lambda^2 + inmats[3]\\lambda^3 + ...)x = 0
        $$
        """

    @overload
    def __init__(self, A: mat) -> None: ...
    @overload
    def __init__(self, A: mat, B: mat) -> None: ...
    @overload
    def __init__(self, K: mat, C: mat, M: mat) -> None: ...
    @overload
    def __init__(self, inmats: Sequence[mat]) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    def allcompute(
        self,
        relrestol: float,
        maxnumit: int,
        numeigenvaluestocompute: int,
        targetreal: float,
        targetimag: float = 0.0,
        verbosity: int = 1,
    ) -> None:
        """
        This is an iterative eigen solver that attempts to compute the first `numeigenvaluestocompute` eigenvalues
        closest to the given target. Note that the targeted values here are eigenvalues and not eigenfrequencies.
        There is no guarantee that SLEPc will return the exact number of eigenvalues requested.
        This can be used on both non-DDM and DDM simulation setup.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcompute(1e-6, 1000, 5, 0)

        See Also
        --------
        eigenvalue.compute, eigenvalue.allcomputeeigenfrequencies
        """
        ...

    def allcomputeeigenfrequencies(
        self,
        relrestol: float,
        maxnumit: int,
        numeigenfrequenciestocompute: int,
        targeteigenfrequencyreal: float = 0.0,
        targeteigenfrequencyimag: float = 0.0,
        verbosity: int = 1,
    ) -> None:
        """
        This is an iterative eigen solver that attempts to compute the first `numeigenfrequenciestocompute` eigenfrequencies
        whose magnitude is closest to a `targeteigenfrequency` ($0.0$ by default). Note that the targeted values are
        eigenfrequencies and not eigenvalues unlike in the `eigenvalue.allcompute` method. There is no guarantee that SLEPc will
        return the exact number of eigenfrequencies requested. This can be used on both non-DDM and DDM simulation setup.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcomputeeigenfrequency(1e-6, 1000, 5, 0)

        See Also
        --------
        eigenvalue.compute, eigenvalue.allcompute
        """
        ...

    def compute(
        self,
        numeigenvaluestocompute: int,
        targetreal: float,
        targetimag: float = 0.0,
        verbosity: int = 1,
    ) -> None: ...
    def count(self) -> int:
        """
        This gets the number of eigenvalues found by SLEPc.
        """
        ...

    def geteigenfrequencies(self) -> list[float]: ...
    def geteigenvalueimaginarypart(self) -> list[float]:
        """
        This gets the imaginary part of all eigenvalues found.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcompute(1e-6, 1000, 5, 0)
        >>>
        >>> eig.printeigenfrequencies()
        >>>
        >>> eigenvalue_real = eig.geteigenvaluerealpart()
        >>> eigenvalue_imag = eig.geteigenvalueimaginarypart()
        >>>
        >>> eigenvector_real = eig.geteigenvectorrealpart()
        >>> eigenvector_imag = eig.geteigenvectorimaginarypart()
        """
        ...

    def geteigenvaluerealpart(self) -> list[float]:
        """
        This gets the real part of all eigenvalues found.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcompute(1e-6, 1000, 5, 0)
        >>>
        >>> eig.printeigenfrequencies()
        >>>
        >>> eigenvalue_real = eig.geteigenvaluerealpart()
        >>> eigenvalue_imag = eig.geteigenvalueimaginarypart()
        >>>
        >>> eigenvector_real = eig.geteigenvectorrealpart()
        >>> eigenvector_imag = eig.geteigenvectorimaginarypart()
        """
        ...

    def geteigenvectorimaginarypart(self) -> list[vec]:
        """
        This gets the imaginary part of all eigenvectors found.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcompute(1e-6, 1000, 5, 0)
        >>>
        >>> eig.printeigenfrequencies()
        >>>
        >>> eigenvalue_real = eig.geteigenvaluerealpart()
        >>> eigenvalue_imag = eig.geteigenvalueimaginarypart()
        >>>
        >>> eigenvector_real = eig.geteigenvectorrealpart()
        >>> eigenvector_imag = eig.geteigenvectorimaginarypart()
        """
        ...

    def geteigenvectorrealpart(self) -> list[vec]:
        """
        This gets the real part of all eigenvectors found.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcompute(1e-6, 1000, 5, 0)
        >>>
        >>> eig.printeigenfrequencies()
        >>>
        >>> eigenvalue_real = eig.geteigenvaluerealpart()
        >>> eigenvalue_imag = eig.geteigenvalueimaginarypart()
        >>>
        >>> eigenvector_real = eig.geteigenvectorrealpart()
        >>> eigenvector_imag = eig.geteigenvectorimaginarypart()
        """
        ...

    def getfdfudbwdrq(self) -> list[list[float]]: ...
    def getqfactors(self) -> list[float]: ...
    def printeigenfrequencies(self) -> None:
        """
        This method provides a convenient way to print the eigenfrequencies associated with all eigenvalues calculated for a
        mechanical resonance problem. In case a generalized eigenvalue problem is used to calculate the resonance modes of an
        undamped mechanical problem, this method displays the resonance frequency of each calculated resonance mode. In case a
        second-order polynomial eigenvalue problem is used to calculate the resonance modes of a damped mechanical problem this
        function displays not only the **damped resonance frequency** of each resonance mode but also the **undamped
        resonance frequency** (only valid in case of proportional damping), the **bandwidth**, the **damping ratio**
        and the **quality factor**.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Direct eigen solver (works only for non-DDM simulation)
        >>> elasticity.generate()
        >>> eig = eigenvalue(elasticity.K(), elasticity.M())
        >>> eig.compute(5, 0)
        >>>
        >>> eig.printeigenfrequencies()
        """
        ...

    def printeigenvalues(self) -> None:
        """
        This prints the eigenvalues found.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Direct eigen solver (works only for non-DDM simulation)
        >>> elasticity.generate()
        >>> eig = eigenvalue(elasticity.K(), elasticity.M())
        >>> eig.compute(5, 0)
        >>>
        >>> eig.printeigenvalues()
        """
        ...

    def settolerance(self, reltol: float, maxnumits: int) -> None:
        """
        This sets the tolerance and maximum number of iterations for the iterative eigen solver. The `settolerance` should be called
        only if `eigenvalue.allcompute` is used to solve the eigen problem.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>>
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 2)
        >>> u.setconstraint(sur)
        >>>
        >>> elasticity = formulation()
        >>>
        >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e-, 0.3))
        >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u))     #  2300 is mass density
        >>>
        >>> # Iterative eigen solver
        >>> eig = eigenvalue(elasticity)
        >>> eig.settolerance(1e-6, 1000)
        >>> eig.allcompute(1e-6, 1000, 5, 0)
        """
        ...
    ...

class expression:
    @overload
    def __add__(self, arg0: expressionlike) -> expression: ...
    @overload
    def __add__(self, arg0: field) -> expression: ...
    @overload
    def __add__(self, arg0: float) -> expression: ...
    @overload
    def __add__(self, arg0: parameter) -> expression: ...
    @overload
    def __add__(self, arg0: port) -> expression: ...
    def __add__(self, *args, **kwargs) -> Any: ...
    @overload
    def __init__(self) -> None:
        """
        The expression object holds a mathematical expression made of operators (such as +, -, *, /), fields, parameters, square
        operators, abs operators and so on.

        Examples
        --------
        An empty expression object can be created as:
        >>> myexpression = expression()

        An expression object can be a scalar:
        >>> myexpression = expression(2)
        >>> myexpression.print()
        Expression size is 1x1
         @ row 0, col 0 :
        2

        An expression object can also be a vector or a 2D array. For this three arguments are required. The first and second arguments
        specify the number of rows and the number of columns respectively. The expression object is filled with input expressions provided
        as a list in the third argument. The general syntax is `expression(numrows:int, numcols:int, input:List[expression]`
        >>> myexpression = expression(1,3, [1,2,3])
        >>> myexpression.print()
        Expression size is 1x3
         @ row 0, col 0 : 1
         @ row 0, col 1 : 2
         @ row 0, col 2 : 3

        In a 2D array expression, the inputs are set in row-major order. In the example below, the entry at the index pair (1,0) in
        the created expression is set to $4$ and the entry (1,2) to $6$.
        $$
        \\begin{bmatrix} 1 & 2 & 3 \\cr 4 & 5 & 6 \\cr 7 & 8 & 9 \\end{bmatrix}
        $$
        >>> myexpression = expression(3,3, [1,2,3, 4,5,6, 7,8,9])   # creates a 3x3 sized expression array
        >>> myexpression.at(1,0).evaluate()
        4.0
        >>> myexpression.at(1,2).evaluate()
        6.0

        A symmetric expression array can also be created by only providing the input list corresponding to the lower triangular part:
        $$
        \\begin{bmatrix} \\color{red}1 & 2 & 4 \\cr \\color{red}2 & \\color{red}3 & 5 \\cr \\color{red}4 & \\color{red}5 & \\color{red}6 \\end{bmatrix}
        $$
        >>> myexpression = expression(3,3, [1, 2,3, 4,5,6])
        >>> myexpression.print()

        A diagonal expression array can also be created by only providing the input list corresponding to the diagonal elements:
        $$
        \\begin{bmatrix} \\color{red}1 & 0 & 0 \\cr 0 & \\color{red}2 & 0 \\cr 0 & 0 & \\color{red}3 \\end{bmatrix}
        $$
        >>> myexpression = expression(3,3, [1,2,3])
        >>> myexpression.print()

        Note that to create a symmetric or diagonal expression array, the size must correspond to a square array (number of rows = number of columns).

        The expression input can also be made of fields. For example:
        >>> mymesh = mesh("disk.msh")
        >>> v = field("h1")
        >>> myexpression = expression(2,3, [12,v,v*(1-v), 3,14-v,0])


        An expression array object can be obtained from the row-wise and column-wise concatenation of input expressions using the syntax
        `expression(input:[List[List[expression]]`. Every element in the argument `input` (i.e. `input[0]`, `input[1]`, ..) is concatenated column-wise with
        others. Every expression in ``input[i]` (i.e `input[i][0]`, `input[i][1]`, ..) is concatenated row-wise with the other expressions in that List.
        $$
        \\begin{bmatrix} \\color{red}1 & \\color{blue}4 & \\color{blue}5 \\cr \\color{red}{2v} & 6 & 7 \\cr \\color{red}3 & 8 & 9 \\end{bmatrix}
        $$
        >>> mymesh = mesh("disk.msh")
        >>> v = field("h1")
        >>> blockleft = expression(3,1, [1,2*v,3])
        >>> blockrighttop = expression(1,2, [4,5])
        >>> blockrightbottom = expression(2,2, [6,7,8,9])
        >>> exprconcatenated = expression([[blockleft], [blockrighttop,blockrightbottom]])
        >>> exprconcatenated.print()
        Expression size is 3x3
         @ row 0, col 0 : 1
         @ row 0, col 1 : 4
         @ row 0, col 2 : 5
         @ row 1, col 0 : field * 2
         @ row 1, col 1 : 6
         @ row 1, col 2 : 7
         @ row 2, col 0 : 3
         @ row 2, col 1 : 8
         @ row 2, col 2 : 9


        It is also useful in many cases to create a conditional expression. It takes the form `expression(condexpr:expression, exprtrue:expression, exprfalse:expression)`.
        If the first argument is greater than equal to zero then the expression is equal to the expression provided in the second argument. If smaller than zero, then it
        is equal to the expression in the third argument.
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>> x = field("x"); y = field("y")
        >>> expr = expression(x+y, 2*x, 0)
        >>> expr.write(top, "conditionalexpr.vtk", 1)
        >>> expr.print()
        Expression size is 1x1
         @ row 0, col 0 : (x + y) ? x * 2, 0)


        An expression can be used to define an algebraic relation between two variables as in the example below:
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>> C = field("h1")         # temperature field in Celsius
        >>> F = field("h1")         # temperature field in Fahrenheit
        >>> F = (9.0/5.0)*C + 32    # Relation for converting Celsius to Fahrenheit
        >>> F.write(top, "F.vtk", 1)

        In the above example, an algebraic relation between two variables was already known allowing us to create an expression that is continuous.
        However, if the data is from an experiment, they are usually not continuous. As an application example, if measurements of a material stiffness (Young's modulus $E$)
        have been performed for a set of temperatures $T$, then only a discrete data set exists between variable $E$ and $T$. A discrete data set can be converted to a
        continuous function ($E$ as a function of $T$) using cubic splines which allows us to interpolate $E$ at any value $T$ in the measured discrete temperature range.
        Using this spline object an expression can be defined that provides cubic spline interpolation of Young's modulus $E$ in the measured discrete temperature range.
        Refer to the `spline` object for more details.

        >>> discrete data set from measurement
        >>> temperature = [273,300,320,340]
        >>> youngsmodulus = [5e9,4e9,5e9,1e9]
        >>>
        >>> spline object: allows interpolation in the measured data range
        >>> spl = spline(temperature, youngsmodulus)
        >>>
        >>> # expression interpolating E at temperature 310.
        >>> # 'spl' holds the interpolation function information.
        >>> E = expression(spl, 310)
        >>> E.print()
        Expression size is 1x1
         @ row 0, col 0 :
        spline(310)
        >>>
        >>> # expression interpolating E for space-dependent temperature profile.
        >>> mymesh = mesh("disk.msh")
        >>> T = field("h1")         # space dependent temperature profile
        >>> E = expression(spl, T)  # space dependent Young's modulus
        >>> E.write(top, "E.vtk", 1)


        The expression object is much more versatile. Say, we have to define an electric supply voltage profile in time that is:
        * 0V for time before 1 sec.
        * increases linearly from 0V to 1V for time range [1,3] sec.
        * 1V for time after 3 sec.
        This can be created as shown below in the example. The following creates a conditional expression for the intervals defined in the first argument for the time
        variable t(). In the below example, the defined interval is [1.0,3.0]. This provides information in three intervals:
        * interval 1: from -$\\infty$ to 1.0
        * interval 2: between 1.0 to 3.0
        * interval 3: from 3.0 to +$\\infty$
        The second argument holds three expressions, each valid in the sequence of the respective interval defined above. The third argument specifies the variable input (time
        in this case). Printing the expression object provides insight into the conditional expression created with these inputs.
        >>> vsupply = expression([1.0,3.0], [0, 0.5*(t()-1), 1.0], t())
        >>> vsupply.print()
        Expression size is 1x1
         @ row 0, col 0 : ((t + -3) ? 1, ((t + -1) ? (t + -1) * 0.5, 0))
        """

    @overload
    def __init__(self, input: field) -> None: ...
    @overload
    def __init__(self, input: float) -> None: ...
    @overload
    def __init__(self, input: parameter) -> None: ...
    @overload
    def __init__(self, input: port) -> None: ...
    @overload
    def __init__(
        self, numrows: int, numcols: int, exprs: Sequence[expressionlike]
    ) -> None: ...
    @overload
    def __init__(self, input: Sequence[Sequence[expressionlike]]) -> None: ...
    @overload
    def __init__(
        self,
        condexpr: expressionlike,
        exprtrue: expressionlike,
        exprfalse: expressionlike,
    ) -> None: ...
    @overload
    def __init__(self, spl: spline, arg: expressionlike) -> None: ...
    @overload
    def __init__(self, grd: grid, args: Sequence[expressionlike]) -> None: ...
    @overload
    def __init__(
        self,
        pos: Sequence[float],
        exprs: Sequence[expressionlike],
        tocompare: expressionlike,
    ) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    @overload
    def __mul__(self, arg0: expressionlike) -> expression: ...
    @overload
    def __mul__(self, arg0: field) -> expression: ...
    @overload
    def __mul__(self, arg0: float) -> expression: ...
    @overload
    def __mul__(self, arg0: parameter) -> expression: ...
    @overload
    def __mul__(self, arg0: port) -> expression: ...
    def __mul__(self, *args, **kwargs) -> Any: ...
    def __neg__(self) -> expression:
        return expression()

    def __pos__(self) -> expression:
        return expression()

    @overload
    def __radd__(self, arg0: float) -> expression: ...
    @overload
    def __radd__(self, arg0: field) -> expression: ...
    @overload
    def __radd__(self, arg0: parameter) -> expression: ...
    @overload
    def __radd__(self, arg0: port) -> expression: ...
    def __radd__(self, *args, **kwargs) -> Any: ...
    @overload
    def __rmul__(self, arg0: float) -> expression: ...
    @overload
    def __rmul__(self, arg0: field) -> expression: ...
    @overload
    def __rmul__(self, arg0: parameter) -> expression: ...
    @overload
    def __rmul__(self, arg0: port) -> expression: ...
    def __rmul__(self, *args, **kwargs) -> Any: ...
    @overload
    def __rsub__(self, arg0: float) -> expression: ...
    @overload
    def __rsub__(self, arg0: field) -> expression: ...
    @overload
    def __rsub__(self, arg0: parameter) -> expression: ...
    @overload
    def __rsub__(self, arg0: port) -> expression: ...
    def __rsub__(self, *args, **kwargs) -> Any: ...
    @overload
    def __rtruediv__(self, arg0: float) -> expression: ...
    @overload
    def __rtruediv__(self, arg0: field) -> expression: ...
    @overload
    def __rtruediv__(self, arg0: parameter) -> expression: ...
    @overload
    def __rtruediv__(self, arg0: port) -> expression: ...
    def __rtruediv__(self, *args, **kwargs) -> Any: ...
    @overload
    def __sub__(self, arg0: expressionlike) -> expression: ...
    @overload
    def __sub__(self, arg0: field) -> expression: ...
    @overload
    def __sub__(self, arg0: float) -> expression: ...
    @overload
    def __sub__(self, arg0: parameter) -> expression: ...
    @overload
    def __sub__(self, arg0: port) -> expression: ...
    def __sub__(self, *args, **kwargs) -> Any: ...
    @overload
    def __truediv__(self, arg0: expressionlike) -> expression: ...
    @overload
    def __truediv__(self, arg0: field) -> expression: ...
    @overload
    def __truediv__(self, arg0: float) -> expression: ...
    @overload
    def __truediv__(self, arg0: parameter) -> expression: ...
    @overload
    def __truediv__(self, arg0: port) -> expression: ...
    def __truediv__(self, *args, **kwargs) -> Any: ...
    def allgridwrite(
        self,
        physreg: int,
        filename: str,
        bounds: Sequence[float],
        numsamples: Sequence[int],
        errorifnotfound: bool = True,
    ) -> None:
        """
        This methods evaluates an expression on a 3D rectilinear grid and writes the evaluated data to the `filename`
        in an **x-major** order.
        The points of the rectilinear grid are found in the `physreg`.
        The X,Y,Z limits of the rectilinear grid is defined by the argument `bounds`.
        The number of grid points in X,Y,Z direction is provided in the `numsamples` argument.
        If a grid point cannot be found (because it is outside of `physreg` or because the interpolation algorithm fails
        to converge, as can happen on curved 3D elements) then an error occurs if `errorifnotfound` argument is set to True.
        If it is set to False, the evaluation of the expression at any non-found grid point is zero, without raising an error.

        Example
        -------
        >>> ...
        >>>
        >>> # define the bounding box limits
        >>> xmin = qs.getx().allmin(reg.polycrystalline_silicon_target, 5)[0]
        >>> xmax = qs.getx().allmax(reg.polycrystalline_silicon_target, 5)[0]
        >>> ymin = qs.gety().allmin(reg.polycrystalline_silicon_target, 5)[0]
        >>> ymax = qs.gety().allmax(reg.polycrystalline_silicon_target, 5)[0]
        >>> zmin = 1e-6
        >>> zmax = 1.5e-6
        >>>
        >>> nx = 1000  # number of samples in X-dreiction
        >>> ny = 1000  # number of samples in Y-dreiction
        >>> nz = 2     # number of samples in Z-dreiction
        >>>
        >>> qs.norm(fld.E)).allgridwrite(reg.air_target, "gridoutput.txt", [xmin,xmax, ymin,ymax, zmin,zmax], [nx, ny, nz])

        See Also
        --------
        grid
        """
        ...

    @overload
    def allintegrate(self, physreg: int, integrationorder: int) -> float:
        """
        This is a collective MPI operation and hence must be called by all ranks. This integrates a **scalar**
        expression over a physical region across all the DDM ranks.

        Note that integration is not allowed on a non-scalar expression.
        Typically `norm` or `comp` functions are used to obtain an equivalent scalar expression from a non-scalar expression to allow integration.

        Integrate `expression(1)` over a 3D/2D/1D physical region to calculate its volume/area/length respectively.
        For axisymmetric problems, the value returned is the integral of the requested expression times the
        coordinate change Jacobian. In the case of axisymmetry, the volume/area/length of the 3D shape corresponding to the
        physical region on which to integrate can be obtained by integrating `expression(1)` and multiplying the output
        by $2\\pi$.

        **Example 1: `allintegrate(physreg:int, integrationorder:int)`**

        The integration is performed over the physical region `physreg`. The integration is exact up to the order of
        polynomials specified in the argument `integrationorder`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> myexpression = expression(12.0)
        >>> integralvalue = myexpression.allintegrate(vol, 4)

        For non-scalar expressions, use `norm` or `comp` to get its scalar equivalent before performing integration.
        >>> vectorexpr = array3x1(10,20,30)
        >>> normintgr = norm(vectorexpr).allintegrate(vol, 4)
        >>> compintgr = comp(0,vectorexpr).allintegrate(vol, 4)

        **Example 2: `allintegrate(physreg:int, meshdeform:expression, integrationorder:int)`**

        Here, the integration is performed on the deformed mesh configuration `meshdeform`.
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> integralvalueondeformedmesh = myexpression.allintegrate(vol, u, 4)

        See Also
        --------
        expression.integrate
        """

    @overload
    def allintegrate(
        self, physreg: int, meshdeform: expressionlike, integrationorder: int
    ) -> float: ...
    def allintegrate(self, *args, **kwargs) -> Any: ...
    @overload
    def allinterpolate(self, physreg: int, xyzcoord: Sequence[float]) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. Its functionality is as described in
        `expression.interpolate` but considers the physical region partitioned across the DDM ranks. The argument must
        `xyzcoord` be the same for all ranks.

        Note that interpolation is allowed for both scalar and non-scalar expressions.

        **Example 1: `allinterpolate(physreg:int, xyzcoord:List[double])`**

        This interpolates the expression at a single point whose [x,y,z] coordinate is provided as an argument.
        The flattened interpolated expression values are returned if the point was found in the elements of the
        physical region `physreg`. If not found an empty list is returned.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x=field("x"); y=field("y"); z=field("z")
        >>> interpolated = array3x1(x,y,z).allinterpolate(vol, [0.5,0.6,0.05])
        >>> interpolated
        [0.5, 0.6, 0.05]

        **Example 2: `allinterpolate(physreg:int, meshdeform:expression, xyzcoord:List[double])`**

        An expression can also be interpolated on a deformed mesh by passing its corresponding field.
        >>> # interpolation on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> interpolated = array3x1(x,y,z).allinterpolate(vol, u, xyzcoord)

        See Also
        --------
        expression.interpolate, expression.alllineinterpolate
        """

    @overload
    def allinterpolate(
        self, physreg: int, meshdeform: expressionlike, xyzcoord: Sequence[float]
    ) -> list[float]: ...
    def allinterpolate(self, *args, **kwargs) -> Any: ...
    def alllineinterpolate(
        self,
        physreg: int,
        firstcoords: Sequence[float],
        lastcoords: Sequence[float],
        numsamples: int,
        errorifnotfound: bool = True,
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. This method interpolates a **scalar**
        expression at a series of points along a line inside a `physreg`. The line for interpolation is defined
        by a starting and an end point whose [x,y,z] coordinates are provided in the `firstcoords` and `lastcoords`
        arguments.
        The `numsamples` argument determines the number of sample points considered along the line.
        If a requested interpolation point along the line cannot be found (because it is outside of `physreg`
        or because the interpolation algorithm fails to converge, as can happen on curved 3D elements) then an
        error occurs if `errorifnotfound` argument is set to True. If it is set to False, the value returned at
        any non-found coordinate is zero, without raising an error.

        Note that interpolation is not allowed on a non-scalar expression.
        Typically `norm` or `comp` functions are used to obtain an equivalent scalar expression from a non-scalar expression to allow interpolation.

        This method in combination with `setoutputvalue` is used to make line plots in post-processing.

        Example
        -------
        >>> ...
        >>>
        >>> form.allsolve(relrestol=1e-06, maxnumit=1000, timestep=1e-6, maxnumnlit=-1)
        >>>
        >>> # parameters for line plot
        >>> xcoord = 0
        >>> ycoord = 0
        >>> zstart = -0.1
        >>> zend = 0.1
        >>> nsamples = 51
        >>> dz = (zend - zstart) / (nsamples - 1)
        >>>
        >>> # Magnetic flux density along Z-axis
        >>> B_axis = qs.norm(df.B).alllineinterpolate(reg.air, [xcoord,ycoord,zstart], [xcoord,ycoord,zend], nsamples, True)
        >>> Z_coords = [zstart+i*dz for i in range(nsamples)]
        >>>
        >>> # Make the interpolated values available for plotting
        >>> qs.setoutputvalue("B_axis",  B_axis, qs.gettime())
        >>> qs.setoutputvalue("Z-coord", Z_coords, qs.gettime())

        See Also
        --------
        expression.interpolate, expression.allinterpolate, setoutputvalue
        """
        ...

    @overload
    def allmax(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. This returns a list with its first element
        containing the maximum value of an expression computed across all the DDM ranks over a geometric region. The remaining
        elements of the list provide the coordinates at which the maximum value was found. This is an overloaded method.

        **Example 1**: `allmax(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The maximum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate maximum value, but
        at an increased computational cost. The maximum value is exact when the refinement nodes added to the elements correspond to
        the position of maximum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the maximum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> maxdata = (2*x).allmax(vol, 1)
        >>> maxdata[0]
        2.0

        The search of the maximum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [maxvalue, xcoordmax, ycoordmax, zcoordmax] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the maximum value.
        >>> maxdatainbox = (2*x).allmax(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `allmax(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The maximum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> maxdataondeformedmesh = (2*x).allmax(vol, u, 1)

        See Also
        --------
        expression.allmin, expression.min, expression.max
        """

    @overload
    def allmax(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def allmax(self, *args, **kwargs) -> Any: ...
    @overload
    def allmin(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. This returns a list with its first element
        containing the minimum value of an expression computed across all the DDM ranks over a geometric region. The remaining
        elements of the list provide the coordinates at which the minimum value was found. This is an overloaded method.

        **Example 1**: `allmin(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The minimum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate minimum value, but
        at an increased computational cost. The minimum value is exact when the refinement nodes added to the elements correspond to
        the position of minimum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the minimum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> mindata = (2*x).allmin(vol, 1)
        >>> mindata[0]
        2.0

        The search of the minimum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [minvalue, xcoordmin, ycoordmin, zcoordmin] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the minimum value.
        >>> mindatainbox = (2*x).allmin(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `allmin(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The minimum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The minimum location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> mindataondeformedmesh = (2*x).allmin(vol, u, 1)

        See Also
        --------
        expression.allmax, expression.max, expression.min
        """

    @overload
    def allmin(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def allmin(self, *args, **kwargs) -> Any: ...
    @overload
    def alltimeinterpolate(
        self, physreg: int, xyzcoord: Sequence[float], numtimesteps: int
    ) -> list[float]: ...
    @overload
    def alltimeinterpolate(
        self,
        physreg: int,
        meshdeform: expressionlike,
        xyzcoord: Sequence[float],
        numtimesteps: int,
    ) -> list[float]: ...
    def alltimeinterpolate(self, *args, **kwargs) -> Any: ...
    def at(self, row: int, col: int) -> expression:
        """
        This returns the entry at the requested row and column.

        Example
        -------
        >>> myexpression = expression(2,2, [1,2, 3,4])
        >>> myexpression.at(0,1)
        2
        """
        return expression()

    def atbarycenter(self, physreg: int, onefield: field) -> vec:
        """
        This outputs a `vec` object whose structure is based on the field argument `onefield` and which contains the expression
        evaluated at the barycenter of each **reference** element of physical region `physreg`. The barycenter of the reference element
        might not be identical to the barycenter of the actual element in the mesh (for curved elements, for general quadrangles,
        hexahedra and prisms). The evaluation at barycenter is constant on each mesh element.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x"); f = field("one")
        >>>
        >>> # Evaluating the expression
        >>> (12*x).write(vol, "expression.vtk", 1)
        >>>
        >>>> # Evaluating the same expression at barycenter
        >>> myvec = (12*x).atbarycenter(vol, f)
        >>> f.setdata(vol, myvec)
        >>> f.write(vol, "barycentervalues.vtk", 1)
        """
        return vec()

    def countcolumns(self) -> int:
        """
        This counts the number of columns in an expression.

        Example
        -------
        >>> myexpression = expression(2,1, [0,1])
        >>> myexpression.countcolumns()
        1
        """
        ...

    def countrows(self) -> int:
        """
        This counts the number of rows in an expression.

        Example
        -------
        >>> myexpression = expression(2,1, [0,1])
        >>> myexpression.countrows()
        2
        """
        ...

    def evaluate(self) -> float:
        """
        This evaluates a scalar, space-independent expression.

        Example
        -------
        >>> settime(0.5)
        >>> expr = 2*abs(-5*t())+3
        >>> expr.evaluate()
        8.0
        """
        ...

    def evaluateharmonics(self) -> list[float]: ...
    def getcolumns(self, colnums: Sequence[int]) -> expression:
        """
        This returns for a matrix expression the columns corresponding to the specified input index `colnums`.

        Example
        -------
        >>> myexpression = expression(3,3, [0,1,2, 3,4,5, 6,7,8])
        >>> subexpr = myexpression.getcolumns([0,2])
        >>> subexpr.print()
        Expression size is 3x2
         @ row 0, col 0 : 0
         @ row 0, col 1 : 2
         @ row 1, col 0 : 3
         @ row 1, col 1 : 5
         @ row 2, col 0 : 6
         @ row 2, col 1 : 8

        See Also
        --------
        getrows
        """
        return expression()

    def getrows(self, rownums: Sequence[int]) -> expression:
        """
        This returns for a matrix expression the rows corresponding to the specified input index `rownums`.

        Example
        -------
        >>> myexpression = expression(3,3, [0,1,2, 3,4,5, 6,7,8])
        >>> subexpr = myexpression.getrows([1,2])
        >>> subexpr.print()
        Expression size is 2x3
         @ row 0, col 0 : 3
         @ row 0, col 1 : 4
         @ row 0, col 2 : 5
         @ row 1, col 0 : 6
         @ row 0, col 1 : 7
         @ row 1, col 2 : 8

        See Also
        --------
        getcolumns
        """
        return expression()

    @overload
    def integrate(self, physreg: int, integrationorder: int) -> float:
        """
        This integrates a **scalar** expression over the physical region `physreg`.

        Note that integration is not allowed on a non-scalar expression.
        Typically `norm` or `comp` functions are used to obtain an equivalent scalar expression from a non-scalar expression to allow integration.

        Integrate `expression(1)` over a 3D/2D/1D physical region to calculate its volume/area/length respectively.
        For axisymmetric problems, the value returned is the integral of the requested expression times the
        coordinate change Jacobian. In the case of axisymmetry, the volume/area/length of the 3D shape corresponding to the
        physical region on which to integrate can be obtained by integrating `expression(1)` and multiplying the output
        by $2\\pi$.

        Be sure to use `expression.allintegrate` if more than one node (i.e. DDM) is used in the simulation.

        **Example 1: `integrate(physreg:int, integrationorder:int)`**

        The integration is performed over the physical region `physreg`. The integration is exact up to the order of
        polynomials specified in the argument `integrationorder`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> myexpression = expression(12.0)
        >>> integralvalue = myexpression.integrate(vol, 4)

        For non-scalar expressions, use `norm` or `comp` to get its scalar equivalent before performing integration.
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> u.setvalue(vol, array3x1(12*x, x*x, 0))
        >>> normintgr = norm(u).integrate(vol, 4)
        >>> compintgr = comp(0,u).integrate(vol, 4)

        **Example 2: `integrate(physreg:int, meshdeform:expression, integrationorder:int)`**

        Here, the integration is performed on the deformed mesh configuration `meshdeform`.
        >>> # integration on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> u.setvalue(vol, array3x1(12*x, x*x, 0))
        >>> integralvalueondeformedmesh = myexpression.integrate(vol, u, 4)

        See Also
        --------
        expression.allintegrate
        """

    @overload
    def integrate(
        self, physreg: int, meshdeform: expressionlike, integrationorder: int
    ) -> float: ...
    def integrate(self, *args, **kwargs) -> Any: ...
    @overload
    def interpolate(self, physreg: int, xyzcoord: Sequence[float]) -> list[float]:
        """
        This interpolates the expression at a single point whose [x,y,z] coordinate is provided as an argument.
        The flattened interpolated expression values are returned if the point was found in the elements of the
        physical region `physreg`. If not found an empty list is returned.

        Note that interpolation is allowed for both scalar and non-scalar expressions.

        Be sure to use `expression.allinterpolate` if more than one node (i.e. DDM) is used in the simulation.

        **Example 1: `interpolate(physreg:int, xyzcoord:List[double])`**
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x=field("x"); y=field("y"); z=field("z")
        >>> interpolated = array3x1(x,y,z).interpolate(vol, [0.5,0.6,0.05])
        >>> interpolated
        [0.5, 0.6, 0.05]


        **Example 2: `interpolate(physreg:int, meshdeform:expression, xyzcoord:List[double])`**

        An expression can also be interpolated on a deformed mesh by passing its corresponding field.
        >>> # interpolation on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> interpolated = array3x1(x,y,z).interpolate(vol, u, xyzcoord)

        See Also
        --------
        expression.allinterpolate, expression.alllineinterpolate
        """

    @overload
    def interpolate(
        self, physreg: int, meshdeform: expressionlike, xyzcoord: Sequence[float]
    ) -> list[float]: ...
    def interpolate(self, *args, **kwargs) -> Any: ...
    def isscalar(self) -> bool:
        """
        This returns True if the expression is a scalar (i.e. has a single row and column).

        Examples
        --------
        >>> myexpression = expression(12.0)
        >>> myexpression.isscalar()
        True
        >>> myexpression = expression(2,2, [0,1, 2,3])
        >>> myexpression.isscalar()
        False
        """
        ...

    def iszero(self) -> bool:
        """
        This returns True if all the entries in the expression is zero, otherwise False.

        Examples
        --------
        >>> myexpression = expression(12.0)
        >>> myexpression.iszero()
        False
        >>> myexpression = expression(0.0)
        >>> myexpression.iszero()
        True
        >>> myexpression = expression(2,2, [0,0, 0,0])
        >>> myexpression.iszero()
        True
        >>> myexpression = expression(2,2, [1,0, 0,0])
        >>> myexpression.iszero()
        False
        """
        ...

    @overload
    def max(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This returns a list with its first element containing the maximum value of an expression computed over a geometric region.
        The remaining elements of the list provide the coordinates at which the maximum value was found. This is an overloaded
        method.

        **Example 1**: `max(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The maximum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate maximum value, but
        at an increased computational cost. The maximum value is exact when the refinement nodes added to the elements correspond to
        the position of maximum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the maximum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> maxdata = (2*x).max(vol, 1)
        >>> maxdata[0]
        2.0

        The search of the maximum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [maxvalue, xcoordmax, ycoordmax, zcoordmax] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the maximum value.
        >>> maxdatainbox = (2*x).max(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `max(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The maximum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> maxdataondeformedmesh = (2*x).max(vol, u, 1)

        See Also
        --------
        expression.min, expression.allmax, expression.allmin
        """

    @overload
    def max(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def max(self, *args, **kwargs) -> Any: ...
    @overload
    def min(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This returns a list with its first element containing the minimum value of an expression computed over a geometric region.
        The remaining elements of the list provide the coordinates at which the minimum value was found. This is an overloaded
        method.

        **Example 1**: `min(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The minimum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate minimum value, but
        at an increased computational cost. The minimum value is exact when the refinement nodes added to the elements correspond to
        the position of minimum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the minimum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> mindata = (2*x).min(vol, 1)
        >>> mindata[0]
        2.0

        The search of the minimum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [minvalue, xcoordmin, ycoordmin, zcoordmin] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the minimum value.
        >>> mindatainbox = (2*x).min(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `min(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The minimum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> mindataondeformedmesh = (2*x).min(vol, u, 1)

        See Also
        --------
        expression.max, expression.allmax, expression.allmin
        """

    @overload
    def min(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def min(self, *args, **kwargs) -> Any: ...
    def print(self) -> None:
        """
        This prints the expression to the console.

        Example
        -------
        >>> myexpression = expression(2,2, [0,1, 2,3])
        >>> myexpression.print()
        Expression size is 2x2
         @ row 0, col 0 : 0
         @ row 0, col 1 : 1
         @ row 1, col 0 : 2
         @ row 1, col 1 : 3
        """
        ...

    def resize(self, numrows: int, numcols: int) -> expression:
        """
        This resizes an expression. Any newly created expression entry is set to zero.

        Example
        -------
        >>> myexpression = expression(2,2, [1,2, 3,4])
        >>> resizedexpr = myexpression.resize(1,3)
        >>> resizedexpr.print()
        Expression size is 1x3
         @ row 0, col 0 : 1
         @ row 0, col 1 : 2
         @ row 0, col 2 : 0
        """
        return expression()

    def reuseit(self, istobereused: bool = True) -> None:
        """
        In case an expression appears multiple times, say in a formulation, and requires much time to compute, then the
        expression can be reused by calling this method and setting `istobereused=True`. With this, the expression is computed
        only once to assemble a formulation block and reused as long as its value remains changed.

        Example
        -------
        >>> myexpression = expression(12.0)
        >>> myexpression.resuseit()     # myexpression.resuseit(True)
        """
        ...

    def rotate(
        self,
        ax: float,
        ay: float,
        az: float,
        leftop: str = "default",
        rightop: str = "default",
    ) -> None:
        """
        This rotates a given expression by `ax`, `ay` and `az` angles about *x*, *y*, *z* axis respectively.

        Let us call $R$ (3x3) the classical 3D rotation matrix used in the transformation of expression written in tensorial
        form and $K$ (6x6) the rotation matrix used in the transformation of expression written in Voigt form.
        For example, the mechanical stress tensor in Voigt form $\\sigma_v$ = ($\\sigma_{xx}, \\sigma_{yy}, \\sigma_{zz},
        \\sigma_{yz}, \\sigma_{zx}, \\sigma_{xy}$) is rotated as $K\\sigma_v$. Matrix $R$ is orthogonal ($R^{-1}$ = $R^{T}$)
        but **matrix $K$ is not orthogonal** ($K^{-1} \\neq K^{T}$).

        This function left-multiplies the calling expression by `lefttop` and right-multiplies it by `righttop` (if any) -
        these arguments depend on the definition of the physics.
        Options for `lefttop`/`righttop` are $^"$ $^"$, $^"R^"$, $^"RT^"$, $^"R$-$1^"$, $^"R$-$T^"$, $^"K^"$, $^"KT^"$, $^"K$-$1^"$, $^"K$-$T^"$
        respectively for a left/right multiplication by nothing $R$, $R^T$, $R^{-1}$, $R^{-T}$, $K$, $K^T$, $K^{-1}$, $K^{-T}$. The function can
        be called without providing the string argument ($^"$default$^"$) to rotate 3x3 tensors and 3x1 vectors (both with the x,y,z component
        ordering).

        The stress tensor in Voigt form $\\sigma_v$ is rotated as $K\\sigma_v$ while the strain tensor in Voigt form $\\epsilon_v$ is rotated as
        $({K^{-1}})^{T}\\epsilon_v$. The rotation of strain Voigt form $K\\epsilon_v$ is different from the stress because  of the factor $2$ added
        to the off-diagonal strain terms. In any case $({K^{-1}})^{T}$ = $({K^{T}})^{-1}$. Denoting the rotated quantities with a prime symbol `,
        one can deduce as an illustration the rotation formulas below.

        In Voigt notation, the rotation of stress tensor $\\sigma_v$ and strain tensor $\\epsilon_v$ is:
        $$
        \\sigma_v^{\\prime} = K \\sigma_v
        $$
        $$
        \\epsilon_v^{\\prime} = (K^{-1})^T \\epsilon_v
        $$

        The elasticity matrix $H$ is such that $\\sigma_v = H\\epsilon_v$ and thus,
        $$
        \\sigma_v = H \\epsilon_v
        $$
        $$
        K^{-1} \\sigma_v^{\\prime} = H K^T \\epsilon_v^{\\prime}
        $$
        $$
        \\sigma_v^{\\prime} = K H K^T \\epsilon_v^{\\prime}
        $$
        $$
        H^{\\prime} = K H K^T
        $$

        Similarly, the compliance matrix C is such that $\\epsilon_v = C \\sigma_v$ and thus,
        $$
        \\epsilon_v = C \\sigma_v
        $$
        $$
        K^T \\epsilon_v^{\\prime} = C K^{-1} \\sigma_v^{\\prime}
        $$
        $$
        \\epsilon_v^{\\prime} = (K^{-1})^T C K^{-1} \\sigma_v^{\\prime}
        $$
        $$
        C^{\\prime} = (K^{-1})^T C K^{-1}
        $$

        The 6x3 piezoelectric coupling matrix [$C/m^2$] relating the electric field $E$ to induced stress is such that
        $\\sigma_v = C E$ and with rotated electric field relation $E^{\\prime} = R E$, we have:
        $$
        \\sigma_v = C E
        $$
        $$
        K^{-1} \\sigma_v^{\\prime} = C R^{-1} E
        $$
        $$
        \\sigma_v^{\\prime} = K C R^{-1} E
        $$
        $$
        \\sigma_v^{\\prime} = K C R^T E
        $$
        $$
        C^{\\prime} = K C R^T
        $$

        Example
        -------
        >>> # Diagonal relative permittivity matrix for PZT
        >>> P = expression(3,3,[1704,1704,1433])
        >>> P = P * 8.854e-12
        >>>
        >>> # Coupling matrix [C/m²] for PZT (6rows, 3columns)
        >>> C = expression(6,3, [0,0,-6.62, 0,0,-6.62, 0,0,23.24, 0,17.03,0, 17.03,0,0, 0,0,0])
        >>>
        >>> # Anisotropic elasticity matrix [Pa] for PZT. Ordering is [exx,eyy,ezz,gyz,gxz,gxy] (Voigt form).
        >>> # Lower triangular part (top to bottom and left to right ) provided since it is symmetric.
        >>> H = expression(6,6, {1.27e11, 8.02e10,1.27e11, 8.46e10,8.46e10,1.17e11, 0,0,0,2.29 e10, 0,0,0,0,2.29 e10, 0,0,0,0,0,2.34 e10});
        >>>
        >>> # Rotate the PZT crystal 45 degress around z
        >>> H.rotate(0,0,45,"K","KT")
        >>> C.rotate(0,0,45,"K","RT")
        >>> P.rotate(0,0,45)
        """
        ...

    def streamline(
        self,
        physreg: int,
        filename: str,
        startcoords: Sequence[float],
        stepsize: float,
        downstreamonly: bool = False,
    ) -> None:
        """
        This follows and writes to disk all paths tangent to the expression vector that are starting at a set of points whose
        $x$, $y$ and $z$ coordinates are provided in `startcoords`. These coordinates can for example be obtained via `.getcoords()`
        on a shape object. A fourth-order Runge-Kutta algorithm is used. The `stepsize` argument is related to the distance between
        two vector direction updates; decrease it to more accurately follow the paths. The paths will be followed as long as they
        remain in the physical region `physreg`. In case the vector norm is zero somewhere on the paths or a path is a closed loop then
        the function might enter an **infinite loop** and never return.
        To use this function on closed loops (for example to get magnetic field lines of a permanent magnet) a solution is to
        break the loops by excluding the permanent magnet domain from the physical region (`selectexclusion`) function can be called
        for that) and set the starting coordinates on the boundary of the magnet.

        Example
        -------
        >>> vol = 1
        >>> mymesh = mesh("disk.msh")
        >>> x=field("x"); y=field("y"); z=field("z")
        >>> startcoords = 12*3*[0.05]   # list of 36 elements with each element value being 0.05
        >>> for i in range(0,12):
        ...     startcoords[3*i+0] += 0.1 + 0.05*i
        >>> array3x1(y+2*x, -y+2*x, 0).streamline(vol, "streamlines.vtk", startcoords, 1.0/100.0)
        """
        ...

    @overload
    def write(
        self, physreg: int, numfftharms: int, filename: str, lagrangeorder: int
    ) -> None:
        """
        This evaluates an expression in the physical region `physreg` and writes it to the file `filename`. The
        `lagrangeorder` is the order of interpolation for evaluation of the expression.

        Examples
        --------
        >>> # setup
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> v = field("h1", [1,2,3])
        >>> u.setorder(vol, 1)
        >>> v.setorder(vol, 1)
        >>>
        >>> # interpolation order for writing an expression
        >>> (1e8*u).write(vol, "uorder1.vtk", 1)    # interpolation order is 1
        >>> (1e8*u).write(vol, "uorder3.vtk", 3)    # interpolation order is 3

        In the example below, an additional integer input $10$ is passed in the second argument. The $10$ here means that
        the expression is treated as multi-harmonic, nonlinear in time variable and an FFT is performed to get the $10$
        first harmonics. All harmonics whose magnitude is above a threshold are saved with '_harm i' extension (except
        for time-constant harmonic).
        >>> abs(v).write(vol, 10, "order1.vtk", 1)  # interpolation order is 1
        >>> (u*u).write(vol, 10, "order3.vtk", 3)   # interpolation order is 3

        In the example below, an additional integer input $50$ is instead passed as the last argument posterior to the
        interpolation order argument. This represents that `numtimesteps` (default=-1). For a positive value of $n$, the
        multi-harmonic expression is saved at $n$ equidistant timesteps in the fundamental period and can then be
        visualized in time.
        >>> (1e8*u).write(vol, "uintime.vtk", 2, 50)

        The expressions can also be evaluated and written on a mesh deformed by a field. If field 'v' is the deformed mesh, then:
        >>> (1e8*u).write(vol, v, "uorder1.vtk", 1)
        >>> (u*u).write(vol, 10, v, "order3.vtk", 3)
        >>> (1e8*u).write(vol, v, "uintime.vtk", 2, 50)
        """

    @overload
    def write(
        self,
        physreg: int,
        numfftharms: int,
        meshdeform: expressionlike,
        filename: str,
        lagrangeorder: int,
    ) -> None: ...
    @overload
    def write(
        self, physreg: int, filename: str, lagrangeorder: int, numtimesteps: int = -1
    ) -> None: ...
    @overload
    def write(
        self,
        physreg: int,
        meshdeform: expressionlike,
        filename: str,
        lagrangeorder: int,
        numtimesteps: int = -1,
    ) -> None: ...
    def write(self, *args, **kwargs) -> Any: ...
    ...

class field:
    @overload
    def __add__(self, arg0: field) -> expression: ...
    @overload
    def __add__(self, arg0: float) -> expression: ...
    @overload
    def __add__(self, arg0: parameter) -> expression: ...
    def __add__(self, *args, **kwargs) -> Any: ...
    @overload
    def __init__(self) -> None:
        """
        The field object holds the information of the finite element fields. The field object itself only holds a pointer to a
        'rawfield' object.

        Examples
        --------
        **Example 1:** `field(fieldtypename:str)`
        >>> mymesh = mesh("disk.h")
        >>> v = field("h1")

        This creates a field object with the specified shape functions. The full list of shape functions available are:
        * Nodal shape functions "h1" e.g. for electrostatic potential and acoustic or fluid pressure.
        * Two-components nodal shape functions "h1xy" e.g. for 2D mechanical displacements and 2D fluid velocity.
        * Three-components nodal shape functions "h1xyz" e.g. for 3D mechanical displacements and 3D fluid velocity.
        * Nedelec's edge shape functions "hcurl" e.g. for the electric field in the E-formulation of electromagnetic wave propagation (here order 0 is allowed).
        * "one", one0", one1", one2", one3" (trailing "xy" or "xyz" allowed) shape functions have a single shape function equal to a constant one on respectively an n, 0, 1, 2, 3-dimensional element (n is the geometry dimension).
        * "h1d", "h1d0", "h1d1", "h1d2", "h1d3" (trailing "xy" or "xyz" allowed) shape functions are elementwise-"h1" shape functions that allow storing fields that are fully discontinuous between elements.

        Additionally, types "x", "y" and "z" can be used to define the x, y and z coordinate fields.
        >>> mymesh = mesh("disk.h")
        >>> x = field("x")
        >>> y = field("y")
        >>> z = field("z")

        **Example 2:** `field(fieldtypename:str, harmonicnumbers:List[int])`
        >>> mymesh = mesh("disk.msh")
        >>> v = field("h1", [1,4,5,6])

        Consider the infinite Fourier series of a field that is periodic in time:
        $$
        v(x, t) = V_1 + V_2 sin(2{\\pi}{f_o}t) + V_3 cos(2{\\pi}{f_o}t) + V_4 sin(2{\\cdot}2{\\pi}{f_o}t) + V_5 cos(2{\\cdot}2{\\pi}{f_o}t) + ..
        $$
        where $t$ is the time variable, $x$ is the space variable and $f_o$ is the fundamental frequency of the periodic field.
        The $V_i$ coefficients only depend on the space variable, not on the time variables which have now moved to the sines and cosines.
        In the example above, field $v$ is a multi-harmonic "h1" type field that includes $4$ harmonic fields: the $V_1$, $V_4$, $V_5$
        and $V_6$ fields in the truncated Fourier series above. All other harmonics in the infinite Fourier series are supposed to equal
        zero so that the field $v$ can be rewritten as:
        $$
        v(x, t) = V_1 + V_4 sin(2{\\cdot}2{\\pi}{f_o}t) + V_5 cos(2{\\cdot}2{\\pi}{f_o}t) + V_6 sin(3{\\cdot}2{\\pi}{f_o}t)
        $$
        This is the truncated multi-harmonic representation of field $v$ (which must be periodic in time).
        The following can be used to get the harmonic $V_4$ from field $v$. It can then be used like any other field.
        >>> v4 = v.harmonic(4)

        **Example 3:** `field(fieldtypename:str, spantree:spanningtree)`
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>> spantree = spanningtree([sur, top])
        >>> a = field("hcurl", spantree)

        This adds the spanning tree input argument needed when the field has to be gauged. (e.g. for the magnetic vector potential
        formulation of the magnetostatic problem in 3D).

        **Example 3:** `field(fieldtypename:str, harmonicnumbers:List[int], spantree:spanningtree)`
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>> spantree = spanningtree([sur, top])
        >>> aharmonic = field("hcurl", [2,3], spantree)

        This adds the spanning tree input argument needed when a $multi-harmonic$ field has to be gauged.
        """

    @overload
    def __init__(self, fieldtypename: str) -> None: ...
    @overload
    def __init__(self, fieldtypename: str, harmonicnumbers: Sequence[int]) -> None: ...
    @overload
    def __init__(self, fieldtypename: str, spantree: spanningtree) -> None: ...
    @overload
    def __init__(
        self, fieldtypename: str, harmonicnumbers: Sequence[int], spantree: spanningtree
    ) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    @overload
    def __mul__(self, arg0: field) -> expression: ...
    @overload
    def __mul__(self, arg0: float) -> expression: ...
    @overload
    def __mul__(self, arg0: parameter) -> expression: ...
    def __mul__(self, *args, **kwargs) -> Any: ...
    def __neg__(self) -> expression:
        return expression()

    def __pos__(self) -> expression:
        return expression()

    @overload
    def __radd__(self, arg0: float) -> expression: ...
    @overload
    def __radd__(self, arg0: parameter) -> expression: ...
    def __radd__(self, *args, **kwargs) -> Any: ...
    @overload
    def __rmul__(self, arg0: float) -> expression: ...
    @overload
    def __rmul__(self, arg0: parameter) -> expression: ...
    def __rmul__(self, *args, **kwargs) -> Any: ...
    @overload
    def __rsub__(self, arg0: float) -> expression: ...
    @overload
    def __rsub__(self, arg0: parameter) -> expression: ...
    def __rsub__(self, *args, **kwargs) -> Any: ...
    @overload
    def __rtruediv__(self, arg0: float) -> expression: ...
    @overload
    def __rtruediv__(self, arg0: parameter) -> expression: ...
    def __rtruediv__(self, *args, **kwargs) -> Any: ...
    @overload
    def __sub__(self, arg0: field) -> expression: ...
    @overload
    def __sub__(self, arg0: float) -> expression: ...
    @overload
    def __sub__(self, arg0: parameter) -> expression: ...
    def __sub__(self, *args, **kwargs) -> Any: ...
    @overload
    def __truediv__(self, arg0: field) -> expression: ...
    @overload
    def __truediv__(self, arg0: float) -> expression: ...
    @overload
    def __truediv__(self, arg0: parameter) -> expression: ...
    def __truediv__(self, *args, **kwargs) -> Any: ...
    @overload
    def allintegrate(self, physreg: int, integrationorder: int) -> float:
        """
        This is a collective MPI operation and hence must be called by all ranks. This integrates a **scalar** field over a
        physical region across all the DDM ranks.

        Note that integration is not allowed on a non-scalar field.
        Typically `norm` or `comp` functions are used to obtain an equivalent scalar field from a non-scalar field to allow integration.

        **Example 1: `allintegrate(physreg:int, integrationorder:int)`**

        The integration is performed over the physical region `physreg`. The integration is exact up to the order of
        polynomials specified in the argument `integrationorder`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x=field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> integralvalue = v.allintegrate(vol, 4)

        For non-scalar fields, use `norm` or `comp` to get its scalar equivalent before performing integration.
        >>> u = field("h1xyz") # vector field with 3 components
        >>> u.setorder(vol, 1)
        >>> ...
        >>> normintgr = norm(u).allintegrate(vol, 4)
        >>> compintgr = comp(0,u).allintegrate(vol, 4)

        **Example 2: `allintegrate(physreg:int, meshdeform:expression, integrationorder:int)`**

        Here, the integration is performed on the deformed mesh configuration `meshdeform`.
        >>> # integrate on a mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> integralvalueondeformedmesh = v.allintegrate(vol, u, 4)

        See Also
        --------
        field.integrate
        """

    @overload
    def allintegrate(
        self, physreg: int, meshdeform: expressionlike, integrationorder: int
    ) -> float: ...
    def allintegrate(self, *args, **kwargs) -> Any: ...
    @overload
    def allinterpolate(self, physreg: int, xyzcoord: Sequence[float]) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. Its functionality is as described in
        `field.interpolate` but considers the physical region partitioned across the DDM ranks. The argument `xyzcoord`
        must be the same for all ranks.

        Note that interpolation is allowed for both scalar and non-scalar fields.

        **Example 1: `allinterpolate(physreg:int, xyzcoord:List[double])`**

        This interpolates the field at a single point whose [x,y,z] coordinate is provided as an argument.
        The flattened interpolated field values are returned if the point was found in the elements of the
        physical region `physreg`. If not found an empty list is returned.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x=field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> xyzcoord = [0.5,0.6,0.05]
        >>>
        >>> interpolated = v.allinterpolate(vol, xyzcoord)
        >>> interpolated
        [5.954696754335098]

        **Example 2: `allinterpolate(physreg:int, meshdeform:expression, xyzcoord:List[double])`**

        A field can also be interpolated on a deformed mesh by passing its corresponding field.
        >>> # interpolation on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> interpolated = u.allinterpolate(vol, u, xyzcoord)

        See Also
        --------
        field.interpolate
        """

    @overload
    def allinterpolate(
        self, physreg: int, meshdeform: expressionlike, xyzcoord: Sequence[float]
    ) -> list[float]: ...
    def allinterpolate(self, *args, **kwargs) -> Any: ...
    def allloadstate(
        self,
        physreg: int,
        statename: str,
        loadportsstate: bool = True,
        errornotvalid: bool = True,
        sourceports: Sequence[port] = [],
        sourceexprs: Sequence[expressionlike] = [],
    ) -> list[float]: ...
    @overload
    def allmax(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. This returns a list with its first element
        containing the maximum value of a field computed across all the DDM ranks over a geometric region. The remaining
        elements of the list provide the coordinates at which the maximum value was found. This is an overloaded method.

        **Example 1: `allmax(physreg:int, refinement:int, xyzrange:List[double]=[])`**

        The maximum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in
        each direction. Increasing the refinement will thus lead to a more accurate maximum value, but at an increased
        computational cost. The maximum value is exact when the refinement nodes added to the elements correspond to the
        position of maximum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the maximum
        is always exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x = field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> maxdata = v.allmax(vol, 1)
        >>> maxdata[0]
        12.0

        The search of the maximum value can be restricted to a box delimited by the last argument `xyzrange` whose form is
        [xboxmin,xboxmax, yboxmin, yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [maxvalue, xcoordmax,
        ycoordmax, zcoordmax] or an empty list if the physical region argument is empty or is not in the box provided. If the
        argument defining the box is not provided, then the whole geometric region is considered for evaluating the maximum
        value.
        >>> ...
        >>> maxdatainbox = v.allmax(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2: `allmax(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`**

        The maximum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location
        and the delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> maxdataondeformedmesh = u.allmax(vol, u, 1)

        See Also
        --------
        field.max, field.min, field.allmin
        """

    @overload
    def allmax(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def allmax(self, *args, **kwargs) -> Any: ...
    @overload
    def allmin(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. This returns a list with its first element
        containing the minimum value of a field computed across all the DDM ranks over a geometric region. The remaining
        elements of the list provide the coordinates at which the minimum value was found. This is an overloaded method.

        **Example 1**: `allmin(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The minimum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in
        each direction. Increasing the refinement will thus lead to a more accurate minimum value, but at an increased
        computational cost. The minimum value is exact when the refinement nodes added to the elements correspond to the
        position of minimum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the minimum
        is always exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x = field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> mindata = v.allmin(vol, 1)
        >>> mindata[0]
        -2.0

        The search of the minimum value can be restricted to a box delimited by the last argument `xyzrange` whose form is
        [xboxmin,xboxmax, yboxmin, yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [minvalue, xcoordmin,
        ycoordmin, zcoordmin] or an empty list if the physical region argument is empty or is not in the box provided. If the
        argument defining the box is not provided, then the whole geometric region is considered for evaluating the minimum
        value.
        >>> ...
        >>> mindatainbox = v.allmin(vol, 5, [-2,0, -2,2, -2,2])

        **Example 2**: `allmin(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The min value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The min location
        and the delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> mindataondeformedmesh = u.allmin(vol, u, 1)

        See Also
        --------
        field.min, field.max, field.allmax
        """

    @overload
    def allmin(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def allmin(self, *args, **kwargs) -> Any: ...
    def allsavestate(
        self,
        physreg: int,
        statename: str,
        saveportsstate: bool = True,
        errornotmatchingvalues: bool = True,
        extradata: Sequence[float] = [],
        sourceports: Sequence[port] = [],
    ) -> None: ...
    @overload
    def alltimeinterpolate(
        self, physreg: int, xyzcoord: Sequence[float], numtimesteps: int
    ) -> list[float]: ...
    @overload
    def alltimeinterpolate(
        self,
        physreg: int,
        meshdeform: expressionlike,
        xyzcoord: Sequence[float],
        numtimesteps: int,
    ) -> list[float]: ...
    def alltimeinterpolate(self, *args, **kwargs) -> Any: ...
    def atbarycenter(self, physreg: int, onefield: field) -> vec:
        """
        This outputs a `vec` object whose structure is based on the field argument `onefield` and which contains the field
        evaluated at the barycenter of each **reference** element of physical region `physreg`. The barycenter of the reference element
        might not be identical to the barycenter of the actual element in the mesh (for curved elements, for general quadrangles,
        hexahedra and prisms). The evaluation at barycenter is constant on each mesh element.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); f = field("one")
        >>> v.setorder(vol, 1)
        >>>
        >>> # Evaluating the field
        >>> v.write(vol, "expression.vtk", 1)
        >>>
        >>>> # Evaluating the same field at barycenter
        >>> myvec = v.atbarycenter(vol, f)
        >>> f.setdata(vol, myvec)
        >>> f.write(vol, "barycentervalues.vtk", 1)
        """
        return vec()

    def automaticupdate(self, updateit: bool) -> None:
        """
        After this call, the field and all its subfields will have their value automatically updated after hp-adaptivity.

        Example
        -------
        >>> ...
        >>> v.automaticupdate()

        See Also
        --------
        field.noautomaticupdate
        """
        ...

    def comp(self, component: int) -> field:
        """
        This gets the $x$, $y$ or $z$ component of a field with subfields.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz")
        >>> ux = u.comp(0)
        >>> uy = u.comp(1)
        >>> uz = u.comp(2)
        """
        return field()

    def compx(self) -> field:
        """
        This gets the $x$ component of a field with multiple subfields.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz")
        >>> ux = u.compx()
        """
        return field()

    def compy(self) -> field:
        """
        This gets the $y$ component of a field with multiple subfields.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz")
        >>> uy = u.compy()
        """
        return field()

    def compz(self) -> field:
        """
        This gets the $z$ component of a field with multiple subfields.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz")
        >>> uz = u.compz()
        """
        return field()

    def copy(self) -> field:
        return field()

    def cos(self, freqindex: int) -> field:
        """
        This gets the "h1xyz" type field that is the $cos$ harmonic at `freqindex` times the fundamental frequency in field $u$.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz", [1,2,3,4,5])
        >>> uc = u.cos(0)   # gets the harmonic 1

        See Also
        --------
        field.sin
        """
        return field()

    def countcomponents(self) -> int:
        """
        This returns the number of components in the field.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> E = field("hcurl")
        >>> numcomp = E.countcomponents()
        >>> numcomp
        3
        """
        ...

    def getharmonics(self) -> list[int]:
        """
        This returns the list of harmonics of the field object.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> v = field("h1", [1,4,5,6])
        >>> myharms = v.getharmonics()
        >>> myharms
        [1, 4, 5, 6]
        """
        ...

    def getnodalvalues(self, nodenumbers: indexmat) -> densemat:
        """
        This gets the values of a "h1" type field at a set of `nodenumbers`.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v.setorder(vol, 1)
        >>> nodenums = indexmat(5,1, [0,1,2,3,4])
        >>> outvals = v.getnodalvalues(nodenums)    # returns a densemat
        >>> outvals.print()
        """
        return densemat()

    def getscale(self) -> float: ...
    def getscales(self) -> list[float]: ...
    @overload
    def harmonic(self, harmonicnumber: int) -> field:
        """
        This gets a "h1xyz" type field that includes the `harmonicnumber(s)`.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz", [1,2,3])
        >>> u2 = u.harmonic(2)      # gets harmonic 2 of field u
        >>> u23 = u.harmonic([1,3]) # gets harmonics 1 and 3 of field u


        This gets a "h1xyz" type field that includes the `harmonicnumber(s)`.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz", [1,2,3])
        >>> u2 = u.harmonic(2)      # gets harmonic 2 of field u
        >>> u23 = u.harmonic([1,3]) # gets harmonics 1 and 3 of field u
        """

    @overload
    def harmonic(self, harmonicnumbers: Sequence[int]) -> field: ...
    def harmonic(self, *args, **kwargs) -> Any: ...
    @overload
    def integrate(self, physreg: int, integrationorder: int) -> float:
        """
        This integrates a **scalar** field over the physical region `physreg`.

        Note that integration is not allowed on a non-scalar field.
        Typically `norm` or `comp` functions are used to obtain an equivalent scalar field from a non-scalar field to allow integration.

        For axisymmetric problems, the value returned is the integral of the requested field times the coordinate change Jacobian.

        Be sure to use `field.allintegrate` if more than one node (i.e. DDM) is used in the simulation.

        **Example 1: `integrate(physreg:int, integrationorder:int)`**

        The integration is performed over the physical region `physreg`. The integration is exact up to the order of
        polynomials specified in the argument `integrationorder`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x=field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> integralvalue = v.integrate(vol, 4)

        For non-scalar fields, use `norm` or `comp` to get its scalar equivalent before performing integration.
        >>> u = field("h1xyz") # vector field with 3 components
        >>> u.setorder(vol, 1)
        >>> ...
        >>> normintgr = norm(u).integrate(vol, 4)
        >>> compintgr = comp(0,u).integrate(vol, 4)

        **Example 2: `integrate(physreg:int, meshdeform:expression, integrationorder:int)`**

        Here, the integration is performed on the deformed mesh configuration `meshdeform`.
        >>> # integrate on a mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> integralvalueondeformedmesh = v.integrate(vol, u, 4)

        See Also
        --------
        field.allintegrate
        """

    @overload
    def integrate(
        self, physreg: int, meshdeform: expressionlike, integrationorder: int
    ) -> float: ...
    def integrate(self, *args, **kwargs) -> Any: ...
    @overload
    def interpolate(self, physreg: int, xyzcoord: Sequence[float]) -> list[float]:
        """
        This interpolates the field value at a single point whose [x,y,z] coordinate is provided as an argument.
        The flattened interpolated field values are returned if the point was found in the elements of the
        physical region `physreg`. If not found an empty list is returned.

        Note that interpolation is allowed for both scalar and non-scalar fields.

        Be sure to use `field.allinterpolate` if more than one node (i.e. DDM) is used in the simulation.

        **Example 1: `interpolate(physreg:int, xyzcoord:List[double])`**

        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x=field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> xyzcoord = [0.5,0.6,0.05]
        >>>
        >>> interpolated = v.interpolate(vol, xyzcoord)
        >>> interpolated
        [5.954696754335098]

        **Example 2: `interpolate(physreg:int, meshdeform:expression, xyzcoord:List[double])`**

        A field can also be interpolated on a deformed mesh by passing its corresponding field.
        >>> # interpolation on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> interpolated = u.interpolate(vol, u, xyzcoord)

        See Also
        --------
        field.allinterpolate
        """

    @overload
    def interpolate(
        self, physreg: int, meshdeform: expressionlike, xyzcoord: Sequence[float]
    ) -> list[float]: ...
    def interpolate(self, *args, **kwargs) -> Any: ...
    def loadraw(self, filename: str, isbinary: bool = False) -> list[float]:
        """
        This loads the .slz file created with the `writeraw` method. If the .slz file was written in the binary format then `isbinary` argument
        must be set to *True* else to *False*. The same mesh must be used when loading with `loadraw` as the one that was used during
        the corresponding `writeraw` call.

        Example
        -------
        >>> vol = 1
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz")
        >>> u.loadraw("v.slz.gz", True)

        See Also
        --------
        field.writeraw
        """
        ...

    @overload
    def max(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This returns a list with its first element containing the maximum value of a field computed over a geometric region.
        The remaining elements of the list provide the coordinates at which the maximum value was found. This is an overloaded
        method.

        **Example 1: `max(physreg:int, refinement:int, xyzrange:List[double]=[])`**

        The maximum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in
        each direction. Increasing the refinement will thus lead to a more accurate maximum value, but at an increased
        computational cost. The maximum value is exact when the refinement nodes added to the elements correspond to the
        position of maximum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the maximum
        is always exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x = field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> maxdata = v.max(vol, 1)
        >>> maxdata[0]
        12.0

        The search of the maximum value can be restricted to a box delimited by the last argument `xyzrange` whose form is
        [xboxmin,xboxmax, yboxmin, yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [maxvalue, xcoordmax,
        ycoordmax, zcoordmax] or an empty list if the physical region argument is empty or is not in the box provided. If the
        argument defining the box is not provided, then the whole geometric region is considered for evaluating the maximum
        value.
        >>> ...
        >>> maxdatainbox = v.max(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2: `max(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`**

        The maximum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location
        and the delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> maxdataondeformedmesh = v.max(vol, u, 1)

        See Also
        --------
        field.min, field.allmax, field.allmin
        """

    @overload
    def max(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def max(self, *args, **kwargs) -> Any: ...
    @overload
    def min(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This returns a list with its first element containing the minimum value of a field computed over a geometric region.
        The remaining elements of the list provide the coordinates at which the minimum value was found. This is an overloaded
        method.

        **Example 1**: `min(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The minimum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in
        each direction. Increasing the refinement will thus lead to a more accurate minimum value, but at an increased
        computational cost. The minimum value is exact when the refinement nodes added to the elements correspond to the
        position of minimum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the minimum
        is always exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); x = field("x")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12*x)
        >>> mindata = v.min(vol, 1)
        >>> mindata[0]
        -2.0

        The search of the minimum value can be restricted to a box delimited by the last argument `xyzrange` whose form is
        [xboxmin,xboxmax, yboxmin, yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [minvalue, xcoordmin,
        ycoordmin, zcoordmin] or an empty list if the physical region argument is empty or is not in the box provided. If the
        argument defining the box is not provided, then the whole geometric region is considered for evaluating the minimum
        value.
        >>> ...
        >>> mindatainbox = v.min(vol, 5, [-2,0, -2,2, -2,2])

        **Example 2**: `min(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The min value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The min location
        and the delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> mindataondeformedmesh = u.min(vol, u, 1)

        See Also
        --------
        field.max, field.allmax, field.allmin
        """

    @overload
    def min(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def min(self, *args, **kwargs) -> Any: ...
    def noautomaticupdate(self) -> None:
        """
        After this call, the field and all its subfields will not have their value automatically updated after hp-adaptivity.
        If the automatic update is not needed then this call is recommended to avoid a possible costly field value update.

        Example
        -------
        >>> ...
        >>> v.noautomaticupdate()

        See Also
        --------
        field.automaticupdate
        """
        ...

    def print(self) -> None:
        """
        This prints the field name.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> v = field("h1")
        >>> v.setname("velocity")
        >>> v.print()
        velocity
        """
        ...

    def printharmonics(self) -> None:
        """
        This prints a string showing the harmonics in the field.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> v = field("h1", [1,4,5,6])
        >>> v.printharmonics()
        +vc0*cos(0*pif0t) +vs2*sin(4*pif0t) +vc2*cos(4*pif0t) +vs3*sin(6*pif0t)
        """
        ...

    def removegauge(self) -> None: ...
    def setcohomologysources(self, cutvalues: Sequence[float]) -> None:
        """
        This method assigns cohomology coefficients to the field. The field value is reset to zero on the cohomology regions before the coefficients
        are added on their respective regions.

        Example
        -------
        >>> mymesh = mesh()
        >>> mymesh.setcohomologycuts([chreg1, chreg2])
        >>> mymesh.load("disk.msh")
        >>> v = field("hcurl")
        >>> ...
        >>> v.setcohomologysources([100, 50])
        >>> v.write(chreg1, "v.pos", 1)
        """
        ...

    @overload
    def setconditionalconstraint(
        self, physreg: int, condexpr: expressionlike, valexpr: expressionlike
    ) -> None:
        """
        This forces the field value (i.e. Dirichlet constraint) on the region `physreg` to a value `valexpr` for all node-associated degrees of
        freedom for which the condition `condexpr` evaluates to greater than or equal to zero at the nodes. This should only be used for fields
        with "h1" type functions.

        **Example 1:** `setconditionalconstraint(physreg: int, condexpr: expression, valexpr: expression)`

        The conditional expression is computed on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; top=3
        >>> v=field("h1"); x=field("x"); y=field("y")
        >>> v.setorder(vol, 1)
        >>> v.setconditionalconstraint(vol, x+y, 12)
        >>>
        >>> form = formulation()
        >>> form += integral(vol, dof(v)*tf(v) - 1*tf(v))
        >>> form.generate()
        >>> sol = solve(form.A(), form.b()) # returns a vec object
        >>> v.setdata(vol, sol)
        >>> v.write(top, "v.vtk", 1)

        **Example 2:** `setconditionalconstraint(physreg: int, meshdeform: expression, condexpr: expression, valexpr: expression)`

        The conditional expression is computed on a mesh deformed by `meshdeform`.
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; top=3
        >>> v=field("h1"); x=field("x"); y=field("y")
        >>> u = field("h1xyz")
        >>> v.setorder(vol, 1)
        >>> v.setconditionalconstraint(vol, u, x+y, 12)
        >>>
        >>> form = formulation()
        >>> form += integral(vol, u, dof(v)*tf(v) - 1*tf(v))
        >>> form.generate()
        >>> sol = solve(form.A(), form.b()) # returns a vec object
        >>> v.setdata(vol, sol)
        >>> v.write(top, "v.vtk", 1)

        See Also
        --------
        field.setconstraint
        """

    @overload
    def setconditionalconstraint(
        self,
        physreg: int,
        meshdeform: expressionlike,
        condexpr: expressionlike,
        valexpr: expressionlike,
    ) -> None: ...
    def setconditionalconstraint(self, *args, **kwargs) -> Any: ...
    @overload
    def setconstraint(
        self, physreg: int, input: expressionlike, extraintegrationdegree: int = 0
    ) -> None:
        """
        This forces the field value (i.e. Dirichlet condition) on the region `physreg` to `input` expression. An extra int argument `extraintegrationdegree`
        can be used to increase or decrease the default integration order when computing the projection of the expression on the field.
        Increasing it can give a more accurate computation of the expression but might take longer. The default integration order is equal
        to "*field order* $\\times 2 + 2$". **Dirichlet constraints have priority over conditional constraints and gauge conditions**.
        Defining any of these on a Dirichlet constrained region has no effect.

        Examples
        --------
        **Example 1:** `field.setconstraint(physreg:int, input:expression, extraintegrationdegree:int=0)`

        This forces the field value (i.e Dirichlet constraint) on region *vol* to `input` expression (here $12+w*w$).
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> w = field("h1")
        >>> v.setconstraint(vol, 12+w*w)


        **Example 2:** `field.setconstraint(physreg:int, meshdeform:expression, input:expression, extraintegrationdegree:int=0)`

        This forces the field value on region *vol* to `input` expression (here $12$) but on a mesh deformed by `meshdeform`.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> u = field("h1xyz")
        >>> v.setconstraint(vol, u, expression(12))


        **Example 3:** `field.setconstraint(physreg:int, input:List[expression], input:expression, extraintegrationdegree:int=0)`

        This sets a Dirichlet constraint with the given value for each corresponding field harmonic.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1", [2,3])
        >>> v.setconstraint(vol, [1,0]) # sets 1 for harmonic 2, 0 for harmonic 3


        **Example 4:** `field.setconstraint(physreg:int, meshdeform:expression, input:List[expression], extraintegrationdegree:int=0)`

        This sets a Dirichlet constraint for each corresponding field harmonic with the given expression computed on a mesh deformed by `meshdeform`.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1", [2,3])
        >>> u = field("h1xyz")
        >>> v.setconstraint(vol, u, [1,0]) # sets 1 for harmonic 2, 0 for harmonic 3


        **Example 5:** `field.setconstraint(physreg:int, numfftharms:int, input:expression, extraintegrationdegree:int=0)`

         This calls an FFT for the calculation required for nonlinear multi-harmonic expressions. The FFT is computed at `numfftharms` timesteps.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v1 = field("h1", [2,3])
        >>> v2 = field("h1", [1,4,5])
        >>> v2.setconstraint(vol, 5, v1*v1)
        >>> v2.write(vol, "v2.vtk", 1)


        **Example 6:** `field.setconstraint(physreg:int, numfftharms:int, meshdeform:expression, input:expression, extraintegrationdegree:int=0)`

        This calls an FFT for the calculation and the expression is evaluated on a mesh deformed by `meshdeform`.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v1 = field("h1", [2,3])
        >>> v2 = field("h1", [1,4,5])
        >>> u = field("h1xyz")
        >>> v2.setconstraint(vol, 5, u, v1*v1)


        **Example 7:** `field.setconstraint(physreg:int)`

        This forces the field value (i.e. Dirichlet condition) on region *vol* to $0$.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setconstraint(vol)


        See Also
        --------
        field.setconditionalconstraint
        """

    @overload
    def setconstraint(
        self,
        physreg: int,
        meshdeform: expressionlike,
        input: expressionlike,
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setconstraint(
        self,
        physreg: int,
        input: Sequence[expressionlike],
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setconstraint(
        self,
        physreg: int,
        meshdeform: expressionlike,
        input: Sequence[expressionlike],
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setconstraint(
        self,
        physreg: int,
        numfftharms: int,
        input: expressionlike,
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setconstraint(
        self,
        physreg: int,
        numfftharms: int,
        meshdeform: expressionlike,
        input: expressionlike,
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setconstraint(self, physreg: int) -> None: ...
    def setconstraint(self, *args, **kwargs) -> Any: ...
    @overload
    def setdata(self, physreg: int, myvec: vec, op: str = "set") -> None:
        """
        This either sets or adds the data in the vector to the field. If the argument `op` is "set", then the vector data is set and if it is
        "add" then the vector data is added to the existing field values. This method only updates the corresponding field values.
        If the formulation uses ports, then `setdata` method must be used to update port values from the solution vector.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1"); w = field("h1")
        >>> v.setorder(vol, 1)
        >>>
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> projection.generate()
        >>> sol = solve(projection.A(), projection.b())
        >>> v.setdata(vol, sol)

        See Also
        --------
        setdata
        """

    @overload
    def setdata(
        self, physreg: int, myvec: vectorfieldselect, op: str = "set"
    ) -> None: ...
    def setdata(self, *args, **kwargs) -> Any: ...
    def setgauge(self, physreg: int) -> None:
        """
        This sets a gauge condition on region`physreg`. It must be used e.g. for the magnetic vector potential formulation of the magnetostatic
        problem in 3D since otherwise, the algebraic system to solve is singular. It is only defined for edge shape functions ("hcurl"). Its
        effect is to constrain to zero all degrees of freedom corresponding to:
        * gradient type shape functions.
        * lowest order edge-shape functions for all edges on the spanning tree provided.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3
        >>> spantree = spanningtree([sur, top])
        >>> a = field("hcurl", spantree)
        >>> a.setgauge(vol)
        """
        ...

    def setname(self, name: str) -> None:
        """
        This gives a name to the field. Useful when printing expressions including fields.

        >>> mymesh = mesh("disk.msh")
        >>> v = field("h1")
        >>> v.setname("velocity")
        >>> v.print()
        velocity
        """
        ...

    def setnodalvalues(self, nodenumbers: indexmat, values: densemat) -> None:
        """
        This sets the values of a "h1" type field at a set of `nodenumbers` to `values`.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> nodenums = indexmat(5,1, [0,1,2,3,4])
        >>> nodevals = densemat(5,1, [10,11,12,13,14])
        >>> v.setnodalvalues(nodenums, nodevals)
        """
        ...

    @overload
    def setorder(self, physreg: int, interpolorder: int) -> None:
        """
        This sets the specified interpolation order of the field object.

        Examples
        --------
        **Example 1:** `field.setorder(physreg:int, interpolorder:int)`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 3)

        This sets the interpolation order to $3$ on the physical region 'vol'.
        When using different interpolation orders on different physical regions for a given field it is only allowed to set the
        interpolation orders in a decreasing way. i.e starting with the physical region with the highest order and ending with the physical
        region with the lowest order. This is required to enforce field continuity and is due to the fact the interpolation order on
        the interface between multiple physical regions must be the one of lowest touching region.

        **Example 2:** `field.setorder(criterion:expression, loworder:int, highorder:int)`
        >>> all=1; inn=2; out=3
        >>> n = 20
        >>> q0 = shape("quadrangle", all, [0,0,0, 1,0,0, 1,0.3,0, 0,0.3,0], [n,n,n,n])
        >>> q1 = shape("quadrangle", all, [1,0,0, 2,0,0, 2,0.3,0, 1,0.3,0], [n,n,n,n])
        >>> linein = q0.getsons()[3]
        >>> linein.setphysicalregion(inn)
        >>> lineout = q1.getsons()[0]
        >>> lineout.setphysicalregion(out)
        >>> mymesh = mesh([q0, q1, linein, lineout])
        >>>
        >>> v = field("h1")
        >>> v.setname("v")
        >>> v.setorder(all, 1)
        >>> v.setorder(norm(grad(v)), 1, 5)
        >>> v.setconstraint(inn, 1)
        >>> v.setconstraint(out)
        >>>
        >>> electrostatics = formulation()
        >>> electrostatics += integral(all, 8.854e-12 * grad(dof(v))*grad(tf(v)))
        >>>
        >>> for i in range(5):
        ...     electrostatics.solve()
        ...     v.write(all, f"v{100+i}.pos", 5)
        ...     (-grad(v)).write(all, f"E{100+i}.pos", 5)
        ...     fieldorder(v).write(all, f"vorder{100+i}.pos", 1)
        ...
        ...     adapt(2)

        In the above example, the field interpolation order will be adapted on each mesh element (of the entire geometry) based on
        the value of a **positive** criterion (p-adaptivity). The max range of the criterion is split into a number of intervals
        equal to the number of orders in range 'loworder' to 'highorder'. All intervals have the same size. The barycenter value of
        the criterion on each mesh element is considered to select the interval, and therefore the corresponding interpolation order
        to assign to the field on each element. As an example, for a criterion with the highest value of 900 over the entire domain and a
        low/high order requested of 1/3 the field on elements with criterion values in range 0 to 300, 300 to 600, 600 to 900 will be
        assigned order 1, 2, 3 respectively.

        **Example 3:** `field.setorder(targeterror:double, loworder:int, highorder:int, absthres:double)`
        >>> sur = 1
        >>> q = shape("quadrangle", sur, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [20,20,20,20])
        >>> mymesh = mesh([q])
        >>> v=field("h1xy"); x=field("x"); y=field("y")
        >>> v.setorder(sur, 1)
        >>> v.setorder(1e-5, 1, 5, 0.001)
        >>> for i in range(5):
        ...     v.setvalue(sur, array2x1(0,cos(10*x*y)))
        ...     adapt()
        ...     v.write(sur, f"v{i}.vtu", 5)
        ...     fieldorder(v).write(sur, f"fov{i}.vtu", 1)

        The field interpolation order will be adapted on each mesh element (of the entire geometry) based on a criterion measuring the
        Legendre expansion decay. The target error gives the fraction of the total shape function weight that does not need to be
        captured. The low order is used on all elements where the total weight is lower than the absolute threshold provided.
        """

    @overload
    def setorder(
        self, criterion: expressionlike, loworder: int, highorder: int
    ) -> None: ...
    @overload
    def setorder(
        self, targeterror: float, loworder: int, highorder: int, absthres: float
    ) -> None: ...
    def setorder(self, *args, **kwargs) -> Any: ...
    def setpatternedport(self, physreg: int, pattern: expressionlike) -> list[port]: ...
    def setport(self, physreg: int, primal: port, dual: port) -> None:
        """
        This function associates a primal-dual pair of ports to the field on the requested physical region. As a side effect, it lowers
        the field order on that region to the minimum possible. **Ports** have priority over Dirichlet constraints, conditional
        constraints and gauge conditions}. Defining any of these on a port region has no effect.

        Ports that have been associated to a field with a *setport* call and unassociated ports are visible to a formulation only if
        they appear in a port relation (in the example below: *electrokinetic += I - 1.0* ). The primal and dual of associated ports are
        always made visible together even if only of them appears in a port relation. Unassociated ports are not connected to the weak
        form terms: the primal can be used as the lumped field value on the associated region while the dual can be used as the total
        contribution over that region of the Neumann term in the formulation. The field value is considered constant by the formulation
        over the region of each associated port visible to it.

        To illustrate the meaning of the dual port let us consider the below DC current flow simulation example code. The strong form to
        solve is
        $$
        \\nabla \\cdot (\\sigma \\nabla v) = 0
        $$

        where $\\sigma$ is the electric conductivity and $v$ is the electric potential field. The corresponding weak form is
        $$
        \\int \\nabla \\cdot (\\sigma \\nabla v) \\ v^{\\prime} d \\Omega = 0
        $$

        which after integration by parts can be rewritten as
        $$
        -\\int_{\\Omega} \\sigma \\nabla v \\cdot  \\nabla v^{\\prime} d \\Omega + \\int_{\\Gamma} \\sigma \\ \\partial_{\\boldsymbol{n}} v \\ v^{\\prime} \\ d \\Gamma = 0
        $$

        where,
        * $\\Gamma$ is the boundary of $\\Omega$,
        * $\\boldsymbol{n}$ is the unit normal pointing outward from $\\Omega$ and
        * $\\sigma \\ \\partial_{\\boldsymbol{n}} v = \\ \\sigma \\ \\nabla v \\cdot {\\boldsymbol{n}} =$ $- \\sigma \\boldsymbol{E} \\cdot \\boldsymbol{n} =$ $- \\boldsymbol{J} \\cdot \\boldsymbol{n}$.

        The Neumann term is the second term of the weak formulation. The dual port $I$ in the below example, therefore equals the total
        current flowing through the electrode and thus $I$ can be used to impose a total current source condition on the electrode.
        More details about the associated mathematics can be found in the paper *'Coupling of local and global quantities in various
        finite element formulations and their application to electrostatics, magnetostatics and magnetodynamics'*, Dular et al.

        Example
        --------
        >>> sur=1; left=2; right=3
        >>> q = shape("quadrangle", sur, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [10,10,10,10])
        >>> ll = q.getsons()[3]
        >>> ll.setphysicalregion(left)
        >>> rl = q.getsons()[1]
        >>> rl.setphysicalregion(right)
        >>> mymesh = mesh([q, ll, rl])
        >>>
        >>> v = field("h1")
        >>> y = field("y")
        >>> v.setorder(sur, 2)
        >>>
        >>> # Electric conductivity increasing with the y-coordinate
        >>> sigma = expression(0.01*(1+2*y))
        >>>
        >>> # Ground the right electrode
        >>> v.setconstraint(right)
        >>>
        >>> V = port()  # primal port
        >>> I = port()  # dual port
        >>> v.setport(left, V, I)
        >>> # The dual port holds the global Neumann term on the port region.
        >>> # For an electrokinetic formulation this equals the total current.
        >>>
        >>> electrokinetic = formulation()
        >>> # Set a 1A current flowing in through the left electrode with the port relation I - 1.0 = 0:
        >>> electrokinetic += I - 1.0    # port relation
        >>> # Define the weak formulation for the DC current flow:
        >>> electrokinetic += integral(sur, -sigma * grad(dof(v) * grad(tf(v))))
        >>>
        >>> electrokinetic.solve()
        >>> v.write(sur, "v.pos", 2)
        >>> (-grad(v)*sigma).write(sur, "j.pos", 2)
        >>>
        >>> resistance = V.getvalue()/I.getvalue()
        >>> print(f"Resistance is {resistance} Ohm")
        """
        ...

    def setscale(self, scale: float) -> None: ...
    def setscales(self, fieldscale: float, neumannscale: float) -> None: ...
    def setupdateaccuracy(self, extraintegrationorder: int) -> None:
        """
        This method allows tuning the integration order in the projection used to update the field value after hp-adaptivity.
        A positive/negative argument increases/decreases the accuracy but slowsdown/speeds up the update.

        Example
        -------
        >>> ...
        >>> v.setupdateaccuracy(2)
        """
        ...

    @overload
    def setvalue(
        self, physreg: int, input: expressionlike, extraintegrationdegree: int = 0
    ) -> None:
        """
        This sets the field value on the region `physreg` to `input` expression. An extra int argument `extraintegrationdegree`
        can be used to increase or decrease the default integration order when computing the projection of the expression on the field.
        Increasing it can give a more accurate computation of the expression but might take longer. The default integration order is equal
        to "*field order* $\\times 2 + 2$".

        Examples
        --------
        **Example 1:** `field.setvalue(physreg:int, input:expression, extraintegrationdegree:int=0)`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, 12)

        This sets the field value on region *vol* to $12$.

        **Example 2:** `field.setvalue(physreg:int, meshdeform:expression, input:expression, extraintegrationdegree:int=0)`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> u = feild("h1xyz")
        >>> v.setorder(vol, 1)
        >>> u.setorder(vol, 1)
        >>> v.setvalue(vol, u, expression(12))

        This sets the field value on region *vol* to expression $12$ but on a mesh deformed by `meshdeform`.

        **Example 3:** `field.setvalue(physreg:int, numfftharms:int, input:expression, extraintegrationdegree:int=0)`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v1 = field("h1", [2,3])
        >>> v2 = field("h1", [1,4,5])
        >>> v1.setorder(vol, 1)
        >>> v2.setorder(vol, 1)
        >>> v2.setvalue(vol, 5, v1*v1)
        >>> v2.write(vol, "v2.vtk", 1)

        This calls an FFT for the calculation required for nonlinear multi-harmonic expressions. The FFT is computed at `numfftharms` timesteps.

        **Example 4:** `field.setvalue(physreg:int, numfftharms:int, meshdeform:expression, input:expression, extraintegrationdegree:int=0)`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v1 = field("h1", [2,3])
        >>> v2 = field("h1", [1,4,5])
        >>> u = field("h1xyz")
        >>> v1.setorder(vol, 1)
        >>> v2.setorder(vol, 1)
        >>> u.setorder(vol, 1)
        >>> v2.setvalue(vol, 5, u, v1*v1)

        This calls an FFT for the calculation and the expression is evaluated on a mesh deformed by `meshdeform`.

        **Example 5:** `field.setvalue(physreg:int)`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol)

        This sets the field value on region *vol* to $0$.
        """

    @overload
    def setvalue(
        self,
        physreg: int,
        meshdeform: expressionlike,
        input: expressionlike,
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setvalue(
        self,
        physreg: int,
        numfftharms: int,
        input: expressionlike,
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setvalue(
        self,
        physreg: int,
        numfftharms: int,
        meshdeform: expressionlike,
        input: expressionlike,
        extraintegrationdegree: int = 0,
    ) -> None: ...
    @overload
    def setvalue(self, physreg: int) -> None: ...
    def setvalue(self, *args, **kwargs) -> Any: ...
    def sin(self, freqindex: int) -> field:
        """
        This gets the "h1xyz" type field that is the $sin$ harmonic at `freqindex` times the fundamental frequency in field $u$.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> u = field("h1xyz", [1,2,3,4,5])
        >>> us = u.sin(2)   # gets the harmonic 4

        See Also
        --------
        field.cos
        """
        return field()

    @overload
    def write(
        self, physreg: int, numfftharms: int, filename: str, lagrangeorder: int
    ) -> None:
        """
        This evaluates a field in the physical region `physreg` and writes it to the file `filename`. The
        `lagrangeorder` is the order of interpolation for the evaluation of the field values.

        Examples
        --------
        >>> # setup
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> v = field("h1", [1,2,3])
        >>> u.setorder(vol, 1)
        >>> v.setorder(vol, 1)
        >>>
        >>> # interpolation order for writing a field
        >>> u.write(vol, "uorder1.vtk", 1)    # interpolation order is 1
        >>> u.write(vol, "uorder3.vtk", 3)    # interpolation order is 3

        In the example below, an additional integer input $10$ is passed in the second argument. The $10$ here means that
        the field is treated as multi-harmonic, nonlinear in time variable and an FFT is performed to get the $10$
        first harmonics. All harmonics whose magnitude is above a threshold are saved with '_harm i' extension (except
        for time-constant harmonic).
        >>> abs(v).write(vol, 10, "order1.vtk", 1)  # interpolation order is 1
        >>> u.write(vol, 10, "order3.vtk", 3)   # interpolation order is 3

        In the example below, an additional integer input $50$ is instead passed as the last argument posterior to the
        interpolation order argument. This represents that `numtimesteps` (default=-1). For a postive value of $n$, the
        multi-harmonic field is saved at $n$ equidistant timestpes in the fundamental period and can then be
        visualized in time.
        >>> u.write(vol, "uintime.vtk", 2, 50)

        The field can also be evaluated and written on a mesh deformed by a field. If field 'v' is the deformed mesh, then:
        >>> u.write(vol, v, "uorder1.vtk", 1)
        >>> u.write(vol, 10, v, "order3.vtk", 3)
        >>> u.write(vol, v, "uintime.vtk", 2, 50)
        """

    @overload
    def write(
        self,
        physreg: int,
        numfftharms: int,
        meshdeform: expressionlike,
        filename: str,
        lagrangeorder: int,
    ) -> None: ...
    @overload
    def write(
        self, physreg: int, filename: str, lagrangeorder: int, numtimesteps: int = -1
    ) -> None: ...
    @overload
    def write(
        self,
        physreg: int,
        meshdeform: expressionlike,
        filename: str,
        lagrangeorder: int,
        numtimesteps: int = -1,
    ) -> None: ...
    def write(self, *args, **kwargs) -> Any: ...
    def writeraw(
        self,
        physreg: int,
        filename: str,
        isbinary: bool = False,
        extradata: Sequence[float] = [],
    ) -> None:
        """
        This writes a (possibly multi-harmonic) field on a given region to disk in the **compact .slz sparselizard format**. If
        `isbinary=False` the output format is in ASCII and with `isbinary=True` the output is in binary format. In the latter case,
        the .slz.gz extension can also be used to write to gz compressed -slz format (the most compact version). While the binary file
        is more compact on disk it might be less portable across different platforms than the ASCII version.
        The last input argument allows storing extra data (timestep, parameter values, ..) that can be loaded back from the
        `loadraw` output.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v=field("h1xyz"); x=field("x"); y=field("y"); z=field("z")
        >>> v.setorder(vol, 2)
        >>> v.setvalue(vol, array3x1(x*x, y*y, z*z))
        >>> v.writeraw(vol, "v.slz.gz", True)

        See Also
        --------
        field.loadraw
        """
        ...
    ...

class formulation:
    def A(self, keepfragments: bool = False, distributed: bool = False) -> mat:
        """
        This gives the matrix $A$ (of $Ax = b$) that was assembled during the `formulation.generate` call. By default the `keepfragments`
        argument is False which means that the generated matrix is no longer kept in the formulation after returning it to a `mat` object.
        However, if you select True for `keepfragments` it means the generated matrix is kept in the formulation and will be added to the
        matrix assembled in any subsequent `formulation.generate` call.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generate()
        >>> A = projection.A();     # equivalent to A = projection.A(keepfragments=False)

        See Also
        --------
        formulation.rhs, formulation.b
        """
        return mat()

    def C(self, keepfragments: bool = False, distributed: bool = False) -> mat:
        """
        This gives the damping matrix $C$ that was assembled during the `formulation.generate` call. The damping matrix $C$ is a
        matrix that is assembled with only those terms in the formulation which have a dof and that dof has a first-order time
        derivative applied to it (i.e $dt$). For multi-harmonic simulations damping matrix $C$ is empty.

        By default, the `keepfragments` argument is False which means that the generated matrix is no longer kept in the formulation after
        returning it to a `mat` object. However, if you select True for `keepfragments` it means the generated matrix is kept in the
        formulation and will be added to the matrix assembled in any subsequent `formulation.generate` call.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generate()
        >>> C = projection.C();     # equivalent to C = projection.C(keepfragments=False)

        See Also
        --------
        formulation.K, formulation.M
        """
        return mat()

    def K(self, keepfragments: bool = False, distributed: bool = False) -> mat:
        """
        This gives the stiffness matrix $K$ that was assembled during the `formulation.generate` call. The stiffness matrix $K$ is a
        matrix that is assembled with only those terms in the formulation which have a dof and that dof has no time derivative applied
        to it. For multi-harmonic formulations, the stiffness matrix $K$ holds the assembly of all the terms.

        By default, the `keepfragments` argument is False which means that the generated matrix is no longer kept in the formulation after
        returning it to a `mat` object. However, if you select True for `keepfragments` it means the generated matrix is kept in the
        formulation and will be added to the matrix assembled in any subsequent `formulation.generate` call.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generate()
        >>> K = projection.K();     # equivalent to K = projection.K(keepfragments=False)

        See Also
        --------
        formulation.C, formulation.M
        """
        return mat()

    def M(self, keepfragments: bool = False, distributed: bool = False) -> mat:
        """
        This gives the mass matrix $M$ that was assembled during the `formulation.generate` call. The mass matrix $M$ is a
        matrix that is assembled with only those terms in the formulation which have a dof and that dof has a second-order
        time derivative applied to it (i.e $dtdt$). For multi-harmonic simulations mass matrix $M$ is empty.

        By default, the `keepfragments` argument is False which means that the generated matrix is no longer kept in the formulation after
        returning it to a `mat` object. However, if you select True for `keepfragments` it means the generated matrix is kept in the
        formulation and will be added to the matrix assembled in any subsequent `formulation.generate` call.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generate()
        >>> M = projection.M();     # equivalent to M = projection.M(keepfragments=False)

        See Also
        --------
        formulation.K, formulation.C
        """
        return mat()

    @overload
    def __iadd__(self, expression: expressionlike) -> formulation: ...
    @overload
    def __iadd__(self, integrationobject: integration) -> formulation: ...
    @overload
    def __iadd__(
        self, integrationobject: Sequence[tuple[integration, preconditioner]]
    ) -> formulation: ...
    @overload
    def __iadd__(self, integrationobject: Sequence[integration]) -> formulation: ...
    @overload
    def __iadd__(
        self,
        input: tuple[
            Sequence[integration],
            Sequence[
                tuple[field, field, int, Sequence[expressionlike], expressionlike, str]
            ],
        ],
    ) -> formulation: ...
    def __iadd__(self, *args, **kwargs) -> Any: ...
    def __init__(self) -> None:
        """
        The formulation object holds the port relations and the weak form terms of the problem to solve.

        The following creates an empty formulation object:
        >>> mymesh = mesh("disk.msh")
        >>> myformulation = formulation()

        Using the `+=` operator, a port relation can be added to the formulation or can be coupled to weak-form terms.

        Examples
        --------
        Adding a port relation to the formulation: `formulation.operator+=(integrationobject: expression)`
        >>> mymesh = mesh("disk.msh")
        >>> A = port(); B = port()
        >>> linearsystem = formulation()
        >>> linearsystem += A + B - 1.0;    # A + B -1 = 0
        >>> linearsystem += B - 5.0;        # B - 5 = 0
        >>> linearsystem.solve()
        >>> A.getvalue()
        -4.0
        >>> B.getvalue()
        5.0

        Adding a weak form term to the formulation: `formulation.operator+=(integration integrationobject)`. All terms are
        added together and their sum equals zero. There are twelve += calls that are listed below.

        **Basic version**

        In the following, the term is assembled for unknowns (dofs) and test functions (tf). The first argument *vol* is the element
        integration region. Hence, the assembly is for integration on all elements in the region *vol*. When no region is specified
        for the `dof` or `tf` then the element integration region (*vol* in this case) is used by default.
        >>> projection += integral(vol, dof(v)*tf(v))   # same as integral(vol, dof(v, vol)*tf(v, vol))

        In the following, the unknowns (dofs) are defined on region *vol* while the test functions are defined only on region *sur*.
        In the third argument, an extra integer is added. This specifies the extra number that should be added to the default integration
        order to perform the numerical integration in the assembly process. The default integration order is equal to (the order of the unknown
        \\+ order of the test function \\+ 2). In case there is no unknown then it is equal to (order of the test function x 2 + 2).
        By increasing the order a more accurate assembly can be obtained, at the expense of an increased assembling time.
        >>> projection += integral(vol, 2*dof(v)*tf(v,sur), +1)

        Each weak form term can be assigned a contribution number or block number. The default value is $0$. In the below example, it is
        set to $2$. This can be of interest when the formulation is generated since one can choose exactly which block numbers to generate
        and which ones to not generate.
        >>> projection += integral(vol, compx(u)*dof(v,sur)*tf(v) - 2*tf(v), +1, 2)

        **Assemble on the mesh deformed by field $u$**
        Assembly of weak form terms can also be performed on the deformed mesh by providing an additional field input as the second argument.
        The following shows the previous 3 examples but with the assembly performed on the mesh deformed by field $u$.
        >>> projection += integral(vol, u, dof(v)*tf(v))
        >>> projection += integral(vol, u, 2*dof(v)*tf(v,sur), +1)
        >>> projection += integral(vol, u, compx(u)*dof(v,sur)*tf(v) - 2*tf(v), +1, 2)

        **Assemble with a call to FFT to compute the first 20 harmonics**
        If the additional input in the second argument is a positive integer a Fast Fourier Transform (FFT) is called during the assembly
        and the first 20 harmonics will be computed. The harmonics whose magnitude is below a threshold are disregarded. This must be
        called when assembling a multi-harmonic formulation term that is nonlinear in the time variable.
        >>> projection += integral(vol, 20, (1-v)*dof(v)*tf(v) + v*tf(v)
        >>> projection += integral(sur, 20, v*v*dof(v)*tf(v) - tf(v), +3)
        >>> projection += integral(vol, 20, v*dof(,sur)*tf(v), +1, 2)

        **Assemble with a call to FFT to compute the first 20 harmonics on the mesh deformed by field $u$**
        Assembly of a multi-harmonic formulation can be performed on the deformed mesh by providing the field input in the third argument.
        >>> projection += integral(vol, 20, u, (1-v)*dof(v)*tf(v) + v*tf(v)
        >>> projection += integral(sur, 20, u, v*v*dof(v)*tf(v) - tf(v), +3)
        >>> projection += integral(vol, 20, u, v*dof(,sur)*tf(v), +1, 2)
        """
        ...

    def allcountdofs(self) -> int:
        """
        This is a collective MPI operation and hence must be called by all the ranks. It returns on every rank the global number of
        degrees of freedom defined in the scattered formulation. The count is exact if for each field the number of unknowns
        associated to each element matches across touching ranks. It is an estimation otherwise.

        Example
        -------
        >>> vol=1; sur=2
        >>> mymesh = mesh("disk.msh")
        >>>
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> numdofs = projection.allcountdofs()

        See Also
        --------
        formulation.countdofs
        """
        ...

    def allneumann(self, bndreg: int, calcreg: int, fld: field) -> field:
        """
        `allneumann` method returns the Neumann term on the boundary `bndreg` associated with the domain `calcreg` and the field `fld`.
        This method is a collective MPI operation and hence must be called by all the ranks.

        In a weak formulation, higher order differential terms are reduced to a lower order by employing integration by parts.
        Consequently, this gives rise to boundary integrals and the term associated with it is referred as Neumann term.

        To illustrate, let us consider the strong form of electrostatics:
        $$
        \\nabla \\cdot (\\epsilon \\nabla v) = 0
        $$
        where,
        *  $\\epsilon$ is the electric permittivity (F/m),
        *  $v$ is the scalar electric potential field (V), and
        *  $v^{\\prime}$ is the test function of field $v$.

        The corresponding weak form is
        $$
        \\int_{\\Omega} \\nabla \\cdot (\\epsilon \\nabla v) \\ v^{\\prime} d \\Omega = 0
        $$

        which after integration by parts can be rewritten as
        $$
        \\int_{\\Omega} -\\epsilon \\nabla v \\cdot  \\nabla v^{\\prime} d \\Omega + \\int_{\\Gamma} (\\epsilon \\nabla v \\cdot {\\boldsymbol{n}}) \\ v^{\\prime} \\ d \\Gamma = 0
        $$

        where,
        * $\\Gamma$ is the boundary of the domain $\\Omega$,
        * $\\boldsymbol{n}$ is the unit normal vector on the boundary $\\Gamma$ pointing outward from the domain $\\Omega$ and
        * $ \\epsilon \\ \\nabla v \\cdot {\\boldsymbol{n}} = - \\epsilon \\boldsymbol{E} \\cdot \\boldsymbol{n}$

        The second term in the weak formulation of electrostatics ($\\epsilon \\nabla v \\cdot {\\boldsymbol{n}}$) is its **Neumann term**.

        If a boundary region is an interface, then it can belong to two different domains with different physics (e.g. conjuagte heat transfer).
        Depending on the physics in the domain the Neumann term is different.
        In such cases. the arguments `calcreg` and `fld` arguments together will determine the correct Neumann term for evaluation.

        Allsolve uses strong coupling and thus, there can be more than one Neumann term (e.g. laminar flow).
        In such cases, the field `fld` argument determines the associated Neumann term.

        Note that this method does not return the value of the boundary integral itself.
        Rather, it returns only the Neumann term in the boundary integral.
        Use `qs.allintegrate` to integrate the Neumann term and obtain the boundary integral value.
        If the Neumann term is a vector, then the integration must be performed on a component of the vector.


        | Physics               | Field              | <div style="width:130px">Neumann term</div>                                                                                        | Interpretation of the Neumann term, Units                                               |
        | --------------------- | ------------------ |----------------------------------------------------------------------------------------------------------------------------------- |---------------------------------------------------------------------------------------- |
        | Solid mechanics       | $\\boldsymbol{u}$  |  $ \\boldsymbol{\\sigma} \\cdot \\boldsymbol{n}                                                                                  $ | Traction force vector on the boundary,                      $\\newline$ $N/m^2$ or $Pa$ |
        | Current flow          | $v$                | -$ \\boldsymbol{j} \\cdot \\boldsymbol{n}                                                                                        $ | Current density entering through the boundary,              $\\newline$ $A/m^2$         |
        | Electrostatics        | $v$                | -$ \\epsilon \\boldsymbol{E} \\cdot \\boldsymbol{n}                                                                              $ | Charge density on the boundary,                             $\\newline$ $C/m^2$         |
        | Magnetism $\\varphi$  | $$\\phi$$          | -$ \\boldsymbol{B} \\cdot \\boldsymbol{n}                                                                                        $ | Magnetic flux density entering through the boundary,        $\\newline$ $Wb/m^2$ or $T$ |
        | Magnetism A           | $\\boldsymbol{A}$  |  $ \\boldsymbol{n} \\times \\boldsymbol{H} \\newline \\boldsymbol{n} \\times \\frac{1}{\\mu}   (\\nabla \\times \\boldsymbol{A}) $ | Tangential component of the magnetic field on the boundary, $\\newline$ $A/m$           |
        | Magnetism H           | $\\boldsymbol{H}$  |  $ \\boldsymbol{n} \\times \\boldsymbol{E} \\newline \\boldsymbol{n} \\times \\frac{1}{\\sigma}(\\nabla \\times \\boldsymbol{H}) $ | Tangential component of the electric field on the boundary, $\\newline$ $V/m$ or $N/C$  |
        | Heat solid            | $T$                | -$ \\boldsymbol{q} \\cdot \\boldsymbol{n}                                                                                        $ | Heat flux entering through the boundary,                    $\\newline$ $W/m^2$         |
        | Heat fluid            | $T$                | -$ \\boldsymbol{q} \\cdot \\boldsymbol{n}                                                                                        $ | Heat flux entering through the boundary,                    $\\newline$ $W/m^2$         |
        | Acoustic waves        | $p$                |  $ \\nabla p \\cdot \\boldsymbol{n}                                                                                              $ | Normal pressure gradient on the boundary                    $\\newline$ $Pa/m$          |
        | Elastic waves         | $\\boldsymbol{u}$  |  $ \\boldsymbol{\\sigma} \\cdot \\boldsymbol{n}                                                                                  $ | Traction force vector on the boundary,                      $\\newline$ $N/m^2$ or $Pa$ |
        | Electromagnetic waves | $\\boldsymbol{E}$  |  $ \\boldsymbol{n} \\times \\frac{1}{\\mu}   (\\nabla \\times \\boldsymbol{E}) = -\\boldsymbol{n} \\times \\frac{\\partial \\boldsymbol{H}}{\\partial t} $ | The negative rate of change of the tangential component of the magnetic field strength, $\\newline$ $(A/m)/s$ |
        | Laminar flow          | $p \\newline \\text{ } \\newline \\text{ } \\newline \\boldsymbol{V}$ | -$ \\rho \\boldsymbol{V} \\cdot \\boldsymbol{n} \\newline \\text{ } \\newline \\text{ } \\newline \\boldsymbol{\\tau} \\cdot \\boldsymbol{n} $ | Mass flow rate entering through the boundary, $kg/(m^2s)$  $\\newline \\text{ } \\newline$ Viscous traction force vector on the boundary, $\\newline$ $N/m^2$ or $Pa$ |

        Note that $\\boldsymbol{n}$ is the boundary normal vector pointing outside of the domain region.
        Therefore, in 3D $\\boldsymbol{n}$ is a surface normal vector pointing outside of a volume region.
        """
        return field()

    @overload
    def allsolve(
        self, relrestol: float, maxnumit: int, soltype: str = "lu", verbosity: int = 1
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all the ranks. This solves the formulation on all the ranks using
        DDM. The initial solution is taken from the fields' state. The relative residual history is returned. This method can be used for
        both linear and nonlinear problems.

        Examples
        --------
        **Example 1:** `formulation.allsolve(relrestol:double, maxnumit:int, soltype:str="lu", verbosity:int=1)`

        This is used for linear problems. The `relrestol` and `maxnumit` arguments correspond to the stopping criteria for DDM solver.
        The DDM iterations stop if either relative residual tolerance is less than `relrestol` or if the number of DDM iteration
        reaches `maxnumit`.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> projection.allsolve(1e-8, 500)
        >>> v.write(vol, f"v_{getrank()}.vtu", 1)

        **Example 2:** `formulation.allsolve(relrestol:double, maxnumit:int, nltol:double, maxnumnlit:int, relaxvalue:double=1, soltype:str="lu", verbosity:int=1)`

        This is used for nonlinear problems. The `relrestol` and `maxnumit` arguments correspond to the stopping criteria for DDM solver.
        The DDM iteration stops if either relative residual tolerance is less than `relrestol` or if the number of DDM iterations reaches
        `maxnumit`. A nonlinear fixed-point iteration is performed for at most `maxnumnlit` or until the relative error (norm of relative
        solution vector change) is smaller than the tolerance prescribed in `nltol`. A relaxation value can be provided with `relaxvalue`
        argument. Usually, a relaxation value less than $1.0$ (under-relaxation) is used to avoid divergence of a solution.
        >>> ...
        >>> projections.allsolve(1e-8, 500, 1e-6, 200, 0.75)
        """

    @overload
    def allsolve(
        self,
        relrestol: float,
        maxnumit: int,
        nltol: float,
        maxnumnlit: int,
        relaxvalue: float = 1.0,
        soltype: str = "lu",
        verbosity: int = 1,
    ) -> int: ...
    @overload
    def allsolve(
        self,
        relrestol: float,
        maxnumit: int,
        nltol: float,
        maxnumnlit: int,
        relaxvalue: float,
        presolve: Sequence[formulation],
        postsolve: Sequence[formulation],
        soltype: str = "lu",
        verbosity: int = 1,
    ) -> int: ...
    @overload
    def allsolve(
        self,
        relrestol: float,
        maxnumit: int,
        nltol: float,
        maxnumnlit: int,
        relaxvalue: float,
        rhsblocks: Sequence[Sequence[int]],
        soltype: str = "lu",
        verbosity: int = 1,
    ) -> list[vec]: ...
    @overload
    def allsolve(
        self,
        relrestol: float,
        maxnumit: int,
        nltol: float,
        maxnumnlit: int,
        relaxvalue: float,
        rhsblocks: Sequence[Sequence[int]],
        presolve: Sequence[formulation],
        postsolve: Sequence[formulation],
        soltype: str = "lu",
        verbosity: int = 1,
    ) -> list[vec]: ...
    def allsolve(self, *args, **kwargs) -> Any: ...
    def b(
        self,
        keepvector: bool = False,
        dirichletandportupdate: bool = True,
        distributed: bool = False,
    ) -> vec:
        """
        This returns the rhs vector $b$ that was assembled during the `formulation.generate` call. By default the `keepvector` argument
        is False which means that the generated rhs vector is no longer kept in the formulation after returning it to a `vec` object.
        However, if you select True for `keepvector` it means the generated rhs vector is kept in the formulation and will be added to
        the rhs vector assembled in any subsequent `formulation.generate` call.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generate()
        >>> b = projection.b();     # equivalent to b = projection.b(keepvector=False)

        See Also
        --------
        formulation.rhs, formulation.A
        """
        return vec()

    def countdofs(self) -> int:
        """
        This returns the number of degrees of freedom defined in the formulation.

        Example
        -------
        >>> vol=1; sur=2
        >>> mymesh = mesh("disk.msh")
        >>>
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> numdofs = projection.countdofs()
        82

        See Also
        --------
        formulation.allcountdofs
        """
        ...

    def estimatecompute(self) -> list[float]: ...
    @overload
    def generate(self) -> None:
        """
        This assembles all the terms in the formulation.

        Examples
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)         # here 0 is the extra integration order, 2 is the block number assigned.
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v)) # default block number is 0
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))         # default block number is 0
        >>>
        >>> projection.generate()

        A block number can be passed as an argument to generate only the necessary terms in the formulation.
        For example, the following generates only the block number 2. (i.e the first integral term)
        >>> projection.generate(2)

        A list of block numbers can also be passed as an argument. For example, the following generates all terms
        with block numbers 0 and 2. For this formulation, it means all terms are generated since these are the only
        block numbers existing.
        and 0 (default) block numbers.
        >>> projection.generate([0,2])

        See Also
        --------
        formulation.generatestiffnessmatrix, formulation.generatedampingmatrix, formulation.generatemassmatrix, formulation.rhs
        """

    @overload
    def generate(self, contributionnumbers: Sequence[int]) -> None: ...
    @overload
    def generate(self, contributionnumber: int) -> None: ...
    def generate(self, *args, **kwargs) -> Any: ...
    def generatedampingmatrix(self) -> None:
        """
        This assembles only those terms in the formulation which have a dof and that dof has a first-order time derivative applied
        to it (i.e $dt$). For multi-harmonic simulations, it generates nothing.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generatedampingmatrix()    # Here it only generates 'dt(dof(v))*tf(v)'

        See Also
        --------
        formulation.generate, formulation.generatestiffnessmatrix, formulation.generatemassmatrix, formulation.rhs
        """
        ...

    def generatejacobian(self) -> None: ...
    def generatemassmatrix(self) -> None:
        """
        This assembles only those terms in the formulation which have a dof and that dof has a second-order time derivative applied
        to it (i.e $dtdt$). For multi-harmonic formulations, it generates nothing.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generatemassmatrix()    # Here it only generates 'dtdt(dof(v))*tf(v)'

        See Also
        --------
        formulation.generate, formulation.generatestiffnessmatrix, formulation.generatedampingmatrix, formulation.rhs
        """
        ...

    def generaterhs(self) -> None:
        """
        This assembles only the terms in the formulation which have no dof.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generaterhs()    # Here it only generates '-2*tf(v)'

        See Also
        --------
        formulation.generate, formulation.generatestiffnessmatrix, formulation.generatedampingmatrix, formulation.generatemassmatrix
        """
        ...

    def generatestiffnessmatrix(self) -> None:
        """
        This assembles only those terms in the formulation which have a dof and that **dof has no time derivative applied to it. For
        multi-harmonic formulations it generates all the terms.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generatestiffnessmatrix()    # Here it only generates dof(v)*tf(v)

        See Also
        --------
        formulation.generate, formulation.generatedampingmatrix, formulation.generatemassmatrix, formulation.rhs
        """
        ...

    def getdoforders(self) -> list[int]: ...
    def getmatrix(
        self,
        KCM: int,
        keepfragments: bool = False,
        additionalconstraints: Sequence[indexmat] = [],
        distributed: bool = False,
        ignoreconstraints: bool = False,
        portsfactor: float = 1.0,
    ) -> mat:
        """
        Depending on `KCM` argument value, it returns the corresponding matrix as follows:
        * $KCM = 0$, returns the stiffness matrix $K$
        * $KCM = 1$, returns the damping matrix $C$
        * $KCM = 2$, returns the mass matrix $M$

        By default, the `keepfragments` argument is False which means that the generated matrix is no longer kept in the formulation after
        returning it to a `mat` object. However, if you select True for `keepfragments` it means the generated matrix is kept in the
        formulation and will be added to the matrix assembled in any subsequent `formulation.generate` call.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generate()
        >>> K = projection.getmatrix(0);     # equivalent to K = projection.getmatrix(KCM=0, keepfragments=False) or just K = projection.K()
        >>> C = projection.getmatrix(1);     # equivalent to C = projection.getmatrix(KCM=1, keepfragments=False) or just C = projection.C()
        >>> M = projection.getmatrix(2);     # equivalent to M = projection.getmatrix(KCM=2, keepfragments=False) or just M = projection.M()

        See Also
        --------
        formulation.K, formulation.C, formulation.M
        """
        return mat()

    def isdofoffields(self, flds: Sequence[field]) -> list[bool]: ...
    def lump(
        self, physregs: Sequence[int], harmonicnumbers: Sequence[int] = []
    ) -> list[field]:
        """
        This defines one lumped field for each requested physical region in `physreg`.
        If `harmonicnumbers` is nonempty, the fields are all defined with these harmonics.

        Example
        -------
        >>> # Suppose a mesh has been loaded with physical regions reg1, reg2, and reg3
        >>> form = qs.formulation()
        >>> lumpfields = form.lump([reg1, reg2, reg3], [2, 3])
        >>>
        >>> # The above amounts to doing the following for each region:
        >>> # lumpfield1 = qs.field("h1", [2, 3])
        >>> # lumpfield1.setorder(reg1, 1)
        >>> # primal = qs.port([2, 3])
        >>> # dual = qs.port([2, 3])
        >>> # lumpfield1.setport(reg1, primal, dual)
        >>> # form += primal + dual

        See Also
        --------
        port, field.setport
        """
        ...

    def rhs(
        self,
        keepvector: bool = False,
        dirichletandportupdate: bool = True,
        distributed: bool = False,
    ) -> vec:
        """
        This returns the rhs vector $b$ that was assembled during the `formulation.generate` call. By default the `keepvector` argument
        is False which means that the generated rhs vector is no longer kept in the formulation after returning it to a `vec` object.
        However, if you select True for `keepvector` it means the generated rhs vector is kept in the formulation and will be added to
        the rhs vector assembled in any subsequent `formulation.generate` call. This is the same as `formulation.b`.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
        >>> projection += integral(vol, dt(dof(v))*tf(v) - 2*tf(v))
        >>> projection += integral(vol, dtdt(dof(v))*tf(v))
        >>>
        >>> projection.generate()
        >>> rhs = projection.rhs();     # equivalent to rhs = projection.rhs(keepvector=False)

        See Also
        --------
        formulation.b, formulation.A
        """
        return vec()

    def setcoarsegrid(
        self,
        coarsegridorderincrease: int = 0,
        coarsegridrelrestol: float = 0.01,
        coarsegridmaxnumits: int = 10,
        coarsegridverbosity: int = 0,
    ) -> None: ...
    def solve(
        self, soltype: str = "lu", blockstoconsider: Sequence[int] = [-1]
    ) -> None:
        """
        This generates the formulation, solves the algebraic problem $Ax = b$ with a direct solver then saves all the data in vector
        $x$ to the fields defined in the formulation.

        The direct solver type can be set to *"lu"* or *"cholesky"* through the `soltype` argument. If the `diagscaling` is set to True, then the diagonal
        scaling preconditioning is applied. The `blockstoconsider` is a list of integral blocks considered for solving. Default is -$1$ meaning all the
        blocks are considered.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> projection.solve();     # equivalent to projection.solve("lu", False, -1);
        >>> v.write(vol, "v.vtu", 1)
        """
        ...
    ...

class genalpha:
    def __init__(
        self, formul: formulation, dtxinit: vec, dtdtxinit: vec, verbosity: int = 3
    ) -> None:
        """
        This defines the genalpha timestepper object to solve in time the formulation `formul` with the fields' state as an initial solution
        for $x$, `dtxinit` for $\\dot{x}$, `dtdtxinit` for $\\ddot{x}$. The `isrhskcmconstant` list can be used to specify whether
        the RHS vector, K matrix, C matrix and M matrix are constant in time or not. However, this argument is optional and
        need not be provided by the user: in which case the timestepper algorithm automatically determines
        at each timestep whether the correponding vector/matrix is constant in time or not. If constant, the generated vector/matrix
        are reused, otherwise, they are regenerated again at each timestep. If the K, C and M matrices are constant in time, the
        factorization of the algebraic problem is also reused.

        >>> timestepper = genalpha(form, vec(form), vec(form))

        The user has the flexibility to specify the `verbosity` and `isrhskcmconstant` argument. For example:
        >>> timestepper = genalpha(form, vec(form), vec(form), verbosity=3, isrhskcmconstant=[False, False, False, False])
        >>> # or
        >>> timestepper = genalpha(form, vec(form), vec(form), 3, [True, True, True, True])
        >>> # or
        >>> timestepper = genalpha(form, vec(form), vec(form), 3, [False, True, False, True])

        The boolean argument in `rhskcconstant[i]`:
        * $i = 0$ corresponds to the rhs vector
        * $i = 1$ corresponds to the K matrix
        * $i = 2$ corresponds to the C matrix
        * $i = 3$ corresponds to the M matrix

        The genalpha object allows performing a generalized alpha time resolution for a problem of the form
        $M\\ddot{x} + C\\dot{x} + Kx = 0$, be it linear or nonlinear. The solutions for $x$ as well as $\\dot{x}$ and $\\ddot{x}$ are
        made available. For nonlinear problems, a fixed-point iteration is performed at every timestep until the relative error (norm
        of relative solution vector change) is less than the prescribed tolerance.

        The generalized alpha method comes with four parameters ($\\beta$, $\\gamma$, $\\alpha_f$ and $\\alpha_m$) that can be tuned to
        adjust the properties of the time resolution method (convergence order, stability, high frequency, damping and so on). When both
        $\\alpha$ parameters are set to zero, a classical Newmark iteration is obtained. By default, the parameters are set to
        ($\\beta = 0.25$, $\\gamma = 0.50$, $\\alpha_f = 0.0$ and $\\alpha_m = 0.0$) which corresponds to an unconditionally stable
        Newmark iteration.

        A convenient way proposed to set the four parameters is to specify a high-frequency dissipation level and let the four
        parameters be deduced accordingly. This gives a set of parameters leading to an unconditionally stable, second-order accurate
        algorithm possessing an optimal combination of high-frequency and low-frequency dissipation. More information on the generalized
        alpha method can be found in the paper *A time integration algorithm for structural dynamics with improved numerical dissipation:
        the generalized-alpha method*.

        Note that even if the rhs vector can be reused the Dirichlet constraints will nevertheless be recomputed at each timestep.
        """
        ...

    def allgatherextrapolationdata(
        self, skinregion: int, region: int, fld: field
    ) -> list[field]: ...
    @overload
    def allnext(self, relrestol: float, maxnumit: int, timestep: float) -> None:
        """
        This is a collective MPI operation and hence must be called by all ranks. It is similar to the `genalpha.next` function
        but the resolution is performed on all ranks using DDM. This method runs the generalized alpha algorithm for one timestep. After
        the call, the time and field values are updated on all the DDM ranks. This method can be used for both linear and nonlinear
        problems depending on the number of arguments passed.
        The first argument is always `timestep`. Set `timestep=-1` for automatic adaptive timestepping; note that in this case
        it is required to define the rules of adaptivity using `genalpha.setadaptivity` before the timestepping loop.

        Examples
        --------
        **Example 1:** `genalpha.allnext(relrestol: double, maxnumit: int, timestep: double)`

        This is used for linear problems. The `relrestol` and `maxnumit` arguments correspond to the stopping criteria for DDM solver.
        The DDM iterations stop if either relative residual tolerance is less than `relrestol` or if the number of DDM iterations
        reaches `maxnumit`.

        **Example 2:** `genalpha.next(relrestol: double, maxnumit: int, timestep: double, maxnumnlit:int, enforcetolerance:bool=True)`

        This is used for nonlinear problems. The `relrestol` and `maxnumit` arguments correspond to the stopping criteria for DDM solver.
        The DDM iteration stops if either relative residual tolerance is less than `relrestol` or if the number of DDM iterations reaches
        `maxnumit`. A nonlinear fixed-point iteration is performed for at most `maxnumnlit` or until the relative error (norm of relative
        solution vector change) is smaller than the tolerance prescribed in `genalpha.settolerance`.
        This method returns the number of nonlinear iterations performed.

        Set `maxnumnlit=-1` for unlimited nonlinear iterations. The nonlinear iteration will continue to run until the
        convergence (i.e. relative error < desired tolerance) is achieved.

        The `enforcetolerance` by default is set to `True`, in which case an error is thrown if the nonlinear iteration at a
        given timestep does not converge within the `maxnumnlit` iterations.
        If this is set to `False`, no error will be thrown when `maxnumnlit` is reached and the timestepper proceeds to the next timestep.

        In case of automatic adaptive timestepping, the `enforcetolerance=True` will throw an error only after exhausting all options
        (i.e. decreasing timestep to help in convergence) within the rules defined in `genalpha.setadaptivity`.

        See Also
        --------
        genalpha.next
        """

    @overload
    def allnext(
        self,
        relrestol: float,
        maxnumit: int,
        timestep: float,
        maxnumnlit: int,
        enforcetolerance: bool = False,
    ) -> int: ...
    def allnext(self, *args, **kwargs) -> Any: ...
    def count(self) -> int:
        """
        This counts the total number of steps computed.
        """
        ...

    def gettimederivative(self) -> list[vec]:
        """
        This returns a list containing current time derivative solutions. The first element in the list contains the solution of the
        first time derivative $\\dot{x}$ and the second element contains the solution of the second time derivative $\\ddot{x}$.

        See Also
        --------
        genalpha.settimederivative
        """
        ...

    def gettimes(self) -> list[float]:
        """
        This returns all the time values stepped through.
        """
        ...

    def gettimestep(self) -> float:
        """
        This returns the current timestep.
        """
        ...

    def isrhskcmreusable(self) -> list[bool]:
        """
        This returns a list of booleans that provides information about the reusability of the rhs vector, K matrix, C matrix
        and M matrix. They are usually resuable if constant in time otherwise must be regenerated.

        Example
        -------
        >>> timestepper = genalpha(form, vec(form), vec(form))
        >>> ...
        >>> ...
        >>>     timestepper.isrhskcmreusable()
        """
        ...

    @overload
    def next(self, timestep: float) -> None:
        """
        This runs the generalized alpha algorithm for one timestep. After the call, the time and field values are updated. This
        method can be used for both linear and nonlinear problems.
        The first argument is always `timestep`. Set `timestep=-1` for automatic adaptive timestepping; note that in this case
        it is required to define the rules of adaptivity using `genalpha.setadaptivity` before the timestepping loop.

        Examples
        --------
        **Example 1:** `genalpha.next(timestep: double)`

        This is used for linear problems.

        **Example 2:** `genalpha.next(timestep: double, maxnumnlit:int, enforcetolerance:bool=True)`

        This is used for nonlinear problems. A nonlinear fixed-point iteration is performed for at most `maxnumnlit` iterations
        or until the relative error (norm of relative solution vector change) is smaller than the tolerance prescribed in `genalpha.settolerance`.
        This method returns the number of nonlinear iterations performed.

        Set `maxnumnlit=-1` for unlimited nonlinear iterations. The nonlinear iteration will continue to run until the
        convergence (i.e. relative error < desired tolerance) is achieved.

        The `enforcetolerance` by default is set to `True`, in which case an error is thrown if the nonlinear iteration at a
        given timestep does not converge within the `maxnumnlit` iterations.
        If this is set to `False`, no error will be thrown when `maxnumnlit` is reached and the timestepper proceeds to the next timestep.

        In case of automatic adaptive timestepping, the `enforcetolerance=True` will throw an error only after exhausting all options
        (i.e. decreasing timestep to help in convergence) within the rules defined in `genalpha.setadaptivity`.

        See Also
        --------
        genalpha.allnext
        """

    @overload
    def next(
        self, timestep: float, maxnumnlit: int, enforcetolerance: bool = False
    ) -> int: ...
    def next(self, *args, **kwargs) -> Any: ...
    def postsolve(self, formuls: Sequence[formulation]) -> None:
        """
        This defines the set of formulations that must be solved $after$ every resolution of the formulation provided to the
        genalpha constructor. The formulations provided here must lead to a system of the form $Ax = b$ (no damping or mass matrix
        allowed).

        See Also
        --------
        genalpha.presolve
        """
        ...

    def presolve(self, formuls: Sequence[formulation]) -> None:
        """
        This defines the set of formulations that must be solved $before$ every resolution of the formulation provided to the
        genalpha constructor. The formulations provided here must lead to a system of the form $Ax = b$ (no damping or mass matrix
        allowed).

        See Also
        --------
        genalpha.postsolve
        """
        ...

    def setadaptivity(
        self,
        tol: float,
        mints: float,
        maxts: float,
        reffact: float = 0.5,
        coarfact: float = 2.0,
        coarthres: float = 0.5,
        relaxthres: float = 0.7,
    ) -> None:
        """
        This sets the configuration for automatic time adaptivity. The timestep $\\Delta{t}$ will be adjusted between the minimum
        timestep `mints` and maximum timesteps `maxts` to reach the requested relative error tolerance `tol`. To measure the relative
        deviation from a constant time derivative, the relative error is defined as
        $$
        \\Delta{t} \\cdot \\frac{{\\lVert \\dot{x}_{n+1} - \\dot{x}_{n} \\rVert}_2}{{\\lVert x_{n+1} \\rVert}_2}
        $$


        Arguments `reffact` and `coarfact` give the factor to use when the time step is refined or coarsened respectively.
        The timestep is refined when the relative error is above `tol` or when the maximum number of nonlinear iterations is reached.
        The timestep is coarsened when the relative error is below the product `coarthes` $\\times$ `tol` and the nonlinear loop has
        converged in less than the maximum number of iterations.
        """
        ...

    @overload
    def setparameter(self, b: float, g: float, af: float, am: float) -> None:
        """
        This is used to set the parameters of the generalized alpha method.

        To set the four parameters ($\\beta$, $\\gamma$, $\\alpha_f$ and $\\alpha_m$), four arguments are passed, one for each
        parameter:
        >>> genalpha.setparameter(b: double, g: double, ad: double, am: double)

        To set the high-frequency dissipation ($\\rho_{\\infty}$), only one argument is passed:
        >>> genalpha.setparameter(rinf: double)

        The range of high-frequency dissipation is in the range $0 \\leq \\rho_{\\infty} \\leq 1$. The four generalized alpha
        parameters are optimally deduced from ($\\rho_{\\infty}$). The deduced parameters lead to an unconditionally stable,
        second-order accurate algorithm possessing an optimal combination of high-frequency and low-frequency dissipation. Lower
        ($\\rho_{\\infty}$) values lead to more dissipation.
        """

    @overload
    def setparameter(self, rinf: float) -> None: ...
    def setparameter(self, *args, **kwargs) -> Any: ...
    def setrelaxationfactor(self, relaxfact: float) -> None:
        """
        This sets the relaxation factor for the fixed-point nonlinear iteration performed at every timestep for nonlinear problems.
        If the relaxation factor is not set, the default value of $1.0$ is set. If $x_{sol}$ is the solution obtained at a current
        iteration, $x_{old}$ is solution at previous iteration, then the new solution $x_{new}$ at the current iteration is updated as
        $$
        x_{new} = {\\eta} \\ x_{sol} + (1-\\eta)x_{old}
        $$
        where $\\eta$ is the relaxation factor.

        Example
        -------
        >>> timestepper = genalpha(form, vec(form))
        >>> timestepper.settolerance(1e-05)
        >>> timestepper.setrelaxationfactor(-1)
        >>> timestepper.setverbosity(2)

        See Also
        --------
        genalpha.settolerance, genalpha.setverbosity
        """
        ...

    def settimederivative(self, sol: Sequence[vec]) -> None:
        """
        This sets the current solution for the time derivatives $\\dot{x}$ and $\\ddot{x}$ to `sol[0]` and `sol[1]` respectively.

        See Also
        --------
        genalpha.gettimederivative
        """
        ...

    def settimestep(self, timestep: float) -> None:
        """
        This sets the current timestep.
        """
        ...

    def settolerance(self, nltol: float) -> None:
        """
        This sets the tolerance for the fixed-point nonlinear iteration performed at every timestep for nonlinear problems. If the
        tolerance is not set, the default value of $10^{-3}$ is considered.

        Example
        -------
        >>> timestepper = genalpha(form, vec(form))
        >>> timestepper.settolerance(1e-05)
        >>> timestepper.setrelaxationfactor(-1)
        >>> timestepper.setverbosity(2)

        See Also
        --------
        genalpha.setrelaxationfactor, genalpha.setverbosity
        """
        ...

    def setverbosity(self, verbosity: int) -> None:
        """
        This sets the verbosity level. For debugging, higher verbosity is recommended. If the verbosity is not set, the default value
        of $3$ is considered.

        Example
        -------
        >>> timestepper = genalpha(form, vec(form))
        >>> timestepper.settolerance(1e-05)
        >>> timestepper.setrelaxationfactor(-1)
        >>> timestepper.setverbosity(2)

        See Also
        --------
        genalpha.setrelaxationfactor, genalpha.settolerance
        """
        ...
    ...

class grid:
    @overload
    def __init__(self) -> None:
        """
        A grid object allows multivariate interpolation in a rectilinear grid data using bilinear interpolation (for two variates)
        and trilinear interpolation (for three variates). For single variate interpolation refer `spline` class.


        Example
        --------
        >>> # grid ticks for two variates 'a' and 'b'
        >>> a = [0, 0.25, 1, 1.75, 2]
        >>> b = [0, 0.75, 1]
        >>>
        >>> # gridvalues in a-major order
        >>> f = [0, 1.5, 2, 0.25, 1.75, 2.25, 1, 2.5, 3, 1.75, 3.25, 3.75, 2, 3.5, 4]
        >>>
        >>> # grid object holds the interpolation function for the provided rectilinear grid data
        >>> gd = grid(gridticks=[a,b], gridvalues=f)
        >>>
        >>> # expression with spatial interpolation
        >>> gdexpr = qs.expression(gd, [qs.getx(), qs.gety()])

        The above example corresponds to a rectilinear grid data where the function '**f**' value depends on two variates
        '**a**' and '**b**'. The grid object expects that `gridticks` are sorted in ascending order and the`gridvalues` are
        provided in **a-major** order as depicted in the image below. Therefore, the first entry corresponds to the variate
        pair (0,0), the second entry corresponds to the variate pair (0,0.75) and so on.

        ![grid a-major](./imagesAPI/grid_amajor.svg)

        A grid data can be read from a text file. The text file containing the data must be in the following format:

        ![grid_fileformat](./imagesAPI/grid_txtfileformat.svg)

        >>> # grid object from a text file
        >>> gd = grid("f_ab.txt")
        >>>
        >>> # expression with spatial interpolation
        >>> gdexpr = qs.expression(gd, [qs.getx(), qs.gety()])
        """

    @overload
    def __init__(self, filename: str, delimiter: str = "\n") -> None: ...
    @overload
    def __init__(
        self, gridticks: Sequence[Sequence[float]], gridvalues: Sequence[float]
    ) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    def countvariables(self) -> int:
        """
        This returns the number of variates in the rectilinear grid data.

        Example
        -------
        >>> # grid ticks for two variates 'a' and 'b'
        >>> a = [0, 0.25, 1, 1.75, 2]
        >>> b = [0, 0.75, 1]
        >>>
        >>> # gridvalues in a-major order
        >>> f = [0, 1.5, 2, 0.25, 1.75, 2.25, 1, 2.5, 3, 1.75, 3.25, 3.75, 2, 3.5, 4]
        >>>
        >>> # grid object holding an interpolation function for the provided rectilinear grid data
        >>> gd = grid(gridticks=[a,b], gridvalues=f)
        >>>
        >>> numvars = gd.countvariables()
        >>> print(numvars)
        2
        """
        ...

    @overload
    def evalat(self, input: Sequence[float]) -> float:
        """
        For a rectilinear grid object, this method returns interpolated values at given input point(s).

        Examples
        --------
        To interpolate at a single evaluation point:

        >>> # grid ticks for two variates 'a' and 'b'
        >>> a = [0, 0.25, 1, 1.75, 2] # amin=0, amax=2
        >>> b = [0, 0.75, 1]          # bmin=0, bmax=1
        >>>
        >>> # gridvalues in a-major order
        >>> f = [0, 1.5, 2, 0.25, 1.75, 2.25, 1, 2.5, 3, 1.75, 3.25, 3.75, 2, 3.5, 4]
        >>>
        >>> # grid object holding an interpolation function for the provided rectilinear grid data
        >>> gd = grid(gridticks=[a,b], gridvalues=f)
        >>>
        >>> gd.evalat([0,0.75])
        1.5

        To interpolate at multiple evaluation points, the evaluation points are passed as a densemat object.
        - number of rows of densemat = number of evaluation points.
        - number of cols of densemat = number of variates in the rectilinear grid.

        Check `densemat` for reference.

        >>> # interpolation at 4 evaluation points (0,0), (0,0.75), (0,1), (0.25,0)
        >>> # define a 4x2 densemat with each row correspondng to an evaluation point
        >>> B = densemat(4, 2, [0,0, 0,0.75, 0,1, 0.25,0])
        >>> gridinterpolation = gd.evalat(B)
        >>> gridinterpolation.print()
        Matrix size is 4x1
        0
        1.5
        2
        0.25
        """

    @overload
    def evalat(self, input: densemat) -> densemat: ...
    def evalat(self, *args, **kwargs) -> Any: ...
    def getgridmaxs(self) -> list[float]:
        """
        This returns a list of maximum value of each variate in the rectilinear grid data. The length of the list is equal
        to the number of variates.

        Example
        -------
        >>> # grid ticks for two variates 'a' and 'b'
        >>> a = [0, 0.25, 1, 1.75, 2] # amin=0, amax=2
        >>> b = [0, 0.75, 1]          # bmin=0, bmax=1
        >>>
        >>> # gridvalues in a-major order
        >>> f = [0, 1.5, 2, 0.25, 1.75, 2.25, 1, 2.5, 3, 1.75, 3.25, 3.75, 2, 3.5, 4]
        >>>
        >>> # grid object holding an interpolation function for the provided rectilinear grid data
        >>> gd = grid(gridticks=[a,b], gridvalues=f)
        >>>
        >>> gridmaxs = gd.getgridmaxs()
        >>> print(gridmaxs)
        [2.0, 1.0]

        See Also
        --------
        grid.getgridmaxs
        """
        ...

    def getgridmins(self) -> list[float]:
        """
        This returns a list of minimum value of each variate in the rectilinear grid data. The length of the list is equal
        to the number of variates.

        Example
        -------
        >>> # grid ticks for two variates 'a' and 'b'
        >>> a = [0, 0.25, 1, 1.75, 2]
        >>> b = [0, 0.75, 1]
        >>>
        >>> # gridvalues in a-major order
        >>> f = [0, 1.5, 2, 0.25, 1.75, 2.25, 1, 2.5, 3, 1.75, 3.25, 3.75, 2, 3.5, 4]
        >>>
        >>> # grid object holding an interpolation function for the provided rectilinear grid data
        >>> gd = grid(gridticks=[a,b], gridvalues=f)
        >>>
        >>> gridmins = gd.getgridmins()
        >>> print(gridmins)
        [0.0, 0.0]

        See Also
        --------
        grid.getgridmins
        """
        ...

    def set(
        self, gridticks: Sequence[Sequence[float]], gridvalues: Sequence[float]
    ) -> None:
        """
        This method defines a grid object based on the `gridticks` and `gridvalues` provided.

        Example
        -------
        >>> # grid ticks for two variates 'a' and 'b'
        >>> a = [0, 0.25, 1, 1.75, 2]
        >>> b = [0, 0.75, 1]
        >>>
        >>> # gridvalues in a-major order
        >>> f = [0, 1.5, 2, 0.25, 1.75, 2.25, 1, 2.5, 3, 1.75, 3.25, 3.75, 2, 3.5, 4]
        >>>
        >>> # empty grid object
        >>> gd = grid()
        >>>
        >>> # holds an interpolation function for the provided rectilinear grid data
        >>> gd = grid.set(gridticks=[a,b], gridvalues=f)
        >>>
        >>> # expression with spatial interpolation
        >>> gdexpr = qs.expression(gd, [qs.getx(), qs.gety()])

        See Also
        --------
        grid
        """
        ...

    def write(self, filename: str) -> None:
        """
        This writes to the file the original rectilinear grid data.

        Example
        -------
        >>> # grid ticks for two variates 'a' and 'b'
        >>> a = [0, 0.25, 1, 1.75, 2] # amin=0, amax=2
        >>> b = [0, 0.75, 1]          # bmin=0, bmax=1
        >>>
        >>> # gridvalues in a-major order
        >>> f = [0, 1.5, 2, 0.25, 1.75, 2.25, 1, 2.5, 3, 1.75, 3.25, 3.75, 2, 3.5, 4]
        >>>
        >>> # grid object holding an interpolation function for the provided rectilinear grid data
        >>> gd = grid(gridticks=[a,b], gridvalues=f)
        >>>
        >>> gd.write("f_ab.txt")

        The grid data are written to the file in a certain format. For the above example, the written file
        is as shown in the image below (but without the comments).
        ![grid_fileformat](./imagesAPI/grid_txtfileformat.svg)

        See Also
        --------
        expression.allgridwrite
        """
        ...
    ...

class impliciteuler:
    def __init__(self, formul: formulation, dtxinit: vec, verbosity: int = 3) -> None:
        """
        This defines the impliciteuler timestepper object to solve in time the formulation `formul` with the fields' state as an initial
        solution for $x$ and `dtxinit` for $\\dot{x}$. The `isrhskcconstant` list can be used to specify whether the RHS vector,
        K matrix and C matrix are constant in time or not. However, this argument is optional and need not be provided
        by the user: in which case the timestepper algorithm automatically determines at each timestep
        whether the correponding vector/matrix is constant in time or not. If constant, the generated vector/matrix are reused,
        otherwise, they are regenerated again at each timestep. If the K and C matrices are constant in time, the factorization
        of the algebraic problem is also reused.

        >>> timestepper = impliciteuler(form, vec(form))

        The user has the flexibility to specify the `verbosity` and `isrhskcconstant` argument. For example:
        >>> timestepper = impliciteuler(form, vec(form), verbosity=3, isrhskcconstant=[False, False, False])
        >>> # or
        >>> timestepper = impliciteuler(form, vec(form), 3, [True, True, True])
        >>> # or
        >>> timestepper = impliciteuler(form, vec(form), 3, [False, True, False])

        The boolean argument in `rhskcconstant[i]`:
        * $i = 0$ corresponds to the rhs vector
        * $i = 1$ corresponds to the K matrix
        * $i = 2$ corresponds to the C matrix

        The impliciteuler object allows performing an implicit (backward) Euler time resolution for a problem of the form
        $C\\dot{x} + Kx = b$, be it linear or nonlinear. The solutions for $x$, as well as $\\dot{x}$, are made available. For nonlinear
        problems, a fixed-point iteration is performed at every timestep until the relative error (norm of relative solution vector
        change) is less than the prescribed tolerance.
        Note that even if the rhs vector can be reused the Dirichlet constraints will nevertheless be recomputed at each timestep.
        """
        ...

    def allloadstate(self, statename: str) -> None: ...
    @overload
    def allnext(self, relrestol: float, maxnumit: int, timestep: float) -> None:
        """
        This is a collective MPI operation and hence must be called by all ranks. It is similar to the `impliciteuler.next` function
        but the resolution is performed on all ranks using DDM. This method runs the implicit Euler algorithm for one timestep. After
        the call, the time and field values are updated on all the DDM ranks.
        This method can be used for both linear and nonlinear problems depending on the number of arguments passed.
        The first argument is always `timestep`. Set `timestep=-1` for automatic adaptive timestepping; note that in this case
        it is required to define the rules of adaptivity using `impliciteuler.setadaptivity` before the timestepping loop.

        Examples
        --------
        **Example 1:** `impliciteuler.allnext(relrestol: double, maxnumit: int, timestep: double)`

        This is used for linear problems. The `relrestol` and `maxnumit` arguments correspond to the stopping criteria for DDM solver.
        The DDM iterations stop if either relative residual tolerance is less than `relrestol` or if the number of DDM iterations
        reaches `maxnumit`.

        **Example 2:** `impliciteuler.next(relrestol: double, maxnumit: int, timestep: double, maxnumnlit:int, enforcetolerance:bool=True)`

        This is used for nonlinear problems. The `relrestol` and `maxnumit` arguments correspond to the stopping criteria for DDM solver.
        The DDM iteration stops if either relative residual tolerance is less than `relrestol` or if the number of DDM iterations reaches
        `maxnumit`. A nonlinear fixed-point iteration is performed for at most `maxnumnlit` or until the relative error (norm of relative
        solution vector change) is smaller than the tolerance prescribed in `impliciteuler.settolerance`.
        This method returns the number of nonlinear iterations performed.

        Set `maxnumnlit=-1` for unlimited nonlinear iterations. The nonlinear iteration will continue to run until the
        convergence (i.e. relative error < desired tolerance) is achieved.

        The `enforcetolerance` by default is set to `True`, in which case an error is thrown if the nonlinear iteration at a
        given timestep does not converge within the `maxnumnlit` iterations.
        If this is set to `False`, no error will be thrown when `maxnumnlit` is reached and the timestepper proceeds to the next timestep.

        In case of automatic adaptive timestepping, the `enforcetolerance=True` will throw an error only after exhausting all options
        (i.e. decreasing timestep to help in convergence) within the rules defined in `impliciteuler.setadaptivity`.

        See Also
        --------
        impliciteuler.next
        """

    @overload
    def allnext(
        self,
        relrestol: float,
        maxnumit: int,
        timestep: float,
        maxnumnlit: int,
        enforcetolerance: bool = False,
    ) -> int: ...
    def allnext(self, *args, **kwargs) -> Any: ...
    def allsavestate(self, statename: str) -> None: ...
    def count(self) -> int:
        """
        This counts the total number of steps computed.
        """
        ...

    def gettimederivative(self) -> vec:
        """
        This returns the current solution for the first time derivative $\\dot{x}$.

        See Also
        --------
        impliciteuler.settimederivative
        """
        return vec()

    def gettimes(self) -> list[float]:
        """
        This returns all the time values stepped through.
        """
        ...

    def gettimestep(self) -> float:
        """
        This returns the current timestep.
        """
        ...

    def isrhskcreusable(self) -> list[bool]:
        """
        This returns a list of booleans that provides information about the reusability of the rhs vector, K matrix and C matrix.
        They are usually resuable if constant in time otherwise must be regenerated.

        Example
        -------
        >>> timestepper = impliciteuler(form, vec(form), vec(form))
        >>> ...
        >>> ...
        >>>     timestepper.isrhskcreusable()
        """
        ...

    @overload
    def next(self, timestep: float) -> None:
        """
        This runs the implicit Euler algorithm for one timestep. After the call, the time and field values are updated.
        This method can be used for both linear and nonlinear problems depending on the number of arguments passed.
        The first argument is always `timestep`. Set `timestep=-1` for automatic adaptive timestepping; note that in this case
        it is required to define the rules of adaptivity using `impliciteuler.setadaptivity` before the timestepping loop.

        Examples
        --------
        **Example 1:** `implicit.next(timestep: double)`

        This is used for linear problems.

        **Example 2:** `implicit.next(timestep: double, maxnumnlit:int, enforcetolerance:bool=True)`

        This is used for nonlinear problems. A nonlinear fixed-point iteration is performed for at most `maxnumnlit` iterations
        or until the relative error (norm of relative solution vector change) is smaller than the tolerance prescribed in `impliciteuler.settolerance`.
        This method returns the number of nonlinear iterations performed.

        Set `maxnumnlit=-1` for unlimited nonlinear iterations. The nonlinear iteration will continue to run until the
        convergence (i.e. relative error < desired tolerance) is achieved.

        The `enforcetolerance` by default is set to `True`, in which case an error is thrown if the nonlinear iteration at a
        given timestep does not converge within the `maxnumnlit` iterations.
        If this is set to `False`, no error will be thrown when `maxnumnlit` is reached and the timestepper proceeds to the next timestep.

        In case of automatic adaptive timestepping, the `enforcetolerance=True` will throw an error only after exhausting all options
        (i.e. decreasing timestep to help in convergence) within the rules defined in `impliciteuler.setadaptivity`.

        See Also
        --------
        impliciteuler.allnext
        """

    @overload
    def next(
        self, timestep: float, maxnumnlit: int, enforcetolerance: bool = False
    ) -> int: ...
    def next(self, *args, **kwargs) -> Any: ...
    def postsolve(self, formuls: Sequence[formulation]) -> None:
        """
        This defines the set of formulations that must be solved $after$ every resolution of the formulation provided to the
        impliciteuler constructor. The formulations provided here must lead to a system of the form $Ax = b$ (no damping or mass matrix
        allowed).

        See Also
        --------
        impliciteuler.presolve
        """
        ...

    def presolve(self, formuls: Sequence[formulation]) -> None:
        """
        This defines the set of formulations that must be solved $before$ every resolution of the formulation provided to the
        impliciteuler constructor. The formulations provided here must lead to a system of the form $Ax = b$ (no damping or mass matrix
        allowed).

        See Also
        --------
        impliciteuler.postsolve
        """
        ...

    def setadaptivity(
        self,
        tol: float,
        mints: float,
        maxts: float,
        reffact: float = 0.5,
        coarfact: float = 2.0,
        coarthres: float = 0.5,
        relaxthres: float = 0.7,
    ) -> None:
        """
        This sets the configuration for automatic time adaptivity. The timestep $\\Delta{t}$ will be adjusted between the minimum
        timestep `mints` and maximum timesteps `maxts` to reach the requested relative error tolerance `tol`. To measure the relative
        deviation from a constant time derivative, the relative error is defined as
        $$
        \\Delta{t} \\cdot \\frac{{\\lVert \\dot{x}_{n+1} - \\dot{x}_{n} \\rVert}_2}{{\\lVert x_{n+1} \\rVert}_2}
        $$

        Arguments `reffact` and `coarfact` give the factor to use when the time step is refined or coarsened respectively.
        The timestep is refined when the relative error is above `tol` or when the maximum number of nonlinear iterations is reached.
        The timestep is coarsened when the relative error is below the product `coarthes`  $\\times$ `tol` and the nonlinear loop has
        converged in less than the maximum number of iterations.
        """
        ...

    def setrelaxationfactor(self, relaxfact: float) -> None:
        """
        This sets the relaxation factor for the fixed-point nonlinear iteration performed at every timestep for nonlinear problems.
        If the relaxation factor is not set, the default value of $1.0$ is set. If $x_{sol}$ is the solution obtained at a current
        iteration, $x_{old}$ is solution at previous iteration, then the new solution $x_{new}$ at the current iteration is updated as
        $$
        x_{new} = {\\eta} \\ x_{sol} + (1-\\eta)x_{old}
        $$
        where $\\eta$ is the relaxation factor.

        Example
        -------
        >>> timestepper = impliciteuler(form, vec(form))
        >>> timestepper.settolerance(1e-05)
        >>> timestepper.setrelaxationfactor(-1)
        >>> timestepper.setverbosity(2)

        See Also
        --------
        impliciteuler.settolerance, impliciteuler.setverbosity
        """
        ...

    def settimederivative(self, sol: vec) -> None:
        """
        This sets the current solution for the first time derivatives $\\dot{x}$ to `sol[0]`.

        See Also
        --------
        impliciteuler.gettimederivative
        """
        ...

    def settimestep(self, timestep: float) -> None:
        """
        This sets the current timestep.
        """
        ...

    def settolerance(self, nltol: float) -> None:
        """
        This sets the tolerance for the fixed-point nonlinear iteration performed at every timestep for nonlinear problems. If the
        tolerance is not set, the default value of $10^{-3}$ is considered.

        Example
        -------
        >>> timestepper = impliciteuler(form, vec(form))
        >>> timestepper.settolerance(1e-05)
        >>> timestepper.setrelaxationfactor(-1)
        >>> timestepper.setverbosity(2)

        See Also
        --------
        impliciteuler.setrelaxationfactor, impliciteuler.setverbosity
        """
        ...

    def setverbosity(self, verbosity: int) -> None:
        """
        This sets the verbosity level. For debugging, higher verbosity is recommended. If the verbosity is not set, the default value
        of $3$ is considered.

        Example
        -------
        >>> timestepper = impliciteuler(form, vec(form))
        >>> timestepper.settolerance(1e-05)
        >>> timestepper.setrelaxationfactor(-1)
        >>> timestepper.setverbosity(2)

        See Also
        --------
        impliciteuler.setrelaxationfactor, impliciteuler.settolerance
        """
        ...
    ...

class indexmat:
    @overload
    def __init__(self) -> None:
        """
        The `indexmat` object stores a row-major array of integers that corresponds to a dense matrix.
        For storing an array of doubles, see `densemat` object.

        Examples
        --------
        There are many ways of instantiating an `indexmat` object. There are listed below:

        **Example 1**: `indexmat(numberofrows:int, numberofcolumns:int)`
        The following creates a matrix with 2 rows and 3 columns. The entries may be undefined.
        >>> B = indexmat(2,3)

        **Example 2**: `indexmat(numberofrows:int, numberofcolumns:int, initvalue:int)`
        This creates a matrix with 2 rows and 3 columns. All entries are assigned the value `initvalue`.
        >>> B = indexmat(2,3, 12)
        >>> B.print()
        Matrix size is 2x3
        12 12 12
        12 12 12

        **Example 3**: `indexmat(numberofrows:int, numberofcolumns:int, valvec:List[int])`
        This creates a matrix with 2 rows and 3 columns. The entries are assigned the values of `valvec`.
        The length of `valvec` is expected to be equal to the total count of entries in the matrix. So for creating
        a matrix of size $2 \\times 3$, length of `valvec` must be 6.
        >>> B = indexmat(2,3, [1,2,3,4,5,6])
        >>> B.print()
        Matrix size is 2x3
        1 2 3
        4 5 6

        **Example 4**: `indexmat(numberofrows:int, numberofcolumns:int, init:int, step:int)`
        This creates a matrix with 2 rows and 3 columns. The first entry is assigned the value `init` and the consecutive entries
        are assigned values that increase by steps of `step`.
        >>> B = indexmat(2,3, 0, 1)
        >>> B.print()
        Matrix size is 2x3
        0 1 2
        3 4 5

        **Example 5**: `indexmat(input:List[indexmat])`
        This creates a matrix that is the vertical concatenation of `input` matrices. Since the concatenation occurs vertically,
        the number of columns in all the input matrices must match.
        >>> A = indexmat(2,3, 0)
        >>> B = indexmat(1,3, 2)
        >>> AB = indexmat([A,B])
        >>> AB.print()
        Matrix size is 3x3
        0 0 0
        0 0 0
        2 2 2
        """

    @overload
    def __init__(self, numberofrows: int, numberofcolumns: int) -> None: ...
    @overload
    def __init__(
        self, numberofrows: int, numberofcolumns: int, initvalue: int
    ) -> None: ...
    @overload
    def __init__(
        self, numberofrows: int, numberofcolumns: int, valvec: Sequence[int]
    ) -> None: ...
    @overload
    def __init__(
        self, numberofrows: int, numberofcolumns: int, init: int, step: int
    ) -> None: ...
    @overload
    def __init__(self, input: Sequence[indexmat]) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    def count(self) -> int:
        """
        This counts and returns the total number of entries in the dense matrix.
        $$
        count = (number \\ of \\ rows) \\times (number \\ of \\ columns)
        $$

        Example
        -------
        >>> B = indexmat(2,3)
        >>> B.count()
        6
        """
        ...

    def countcolumns(self) -> int:
        """
        This counts and returns the number of columns in the dense matrix.

        Example
        -------
        >>> B = indexmat(2,3)
        >>> B.countcolumns()
        3
        """
        ...

    def countrows(self) -> int:
        """
        This counts and returns the number of rows in the dense matrix.

        Example
        -------
        >>> B = indexmat(2,3)
        >>> B.countrows()
        2
        """
        ...

    def print(self) -> None:
        """
        This prints the entries of the dense matrix.

        Example
        -------
        >>> B = indexmat(2,3, 0,1)
        >>> B.print()
        Matrix size is 2x3
        0 1 2
        3 4 5
        """
        ...

    def printsize(self) -> None:
        """
        This prints the size of the dense matrix.

        Example
        -------
        >>> B = indexmat(2,3)
        >>> B.printsize()
        Matrix size is 2x3
        """
        ...
    ...

class integration:
    """
    This is an internal container class for integration.
    """

    ...

class iodata:
    def extracttimestep(self, timestepindex: int) -> iodata:
        return iodata()

    def getactiveelementtypes(self) -> list[int]: ...
    def getcoordinates(
        self, elemtypenum: int, timestepindex: int = -1
    ) -> list[densemat]: ...
    def getdata(self, elemtypenum: int, timestepindex: int = -1) -> list[densemat]: ...
    def gettimetags(self) -> list[float]: ...
    ...

class logformat:
    """
    Holds possible log formats

    Members:

      plain

      json
    """

    def __eq__(self, other: object, /) -> bool: ...
    def __getstate__(self, /) -> int: ...
    def __hash__(self, /) -> int: ...
    def __index__(self, /) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self, /) -> int: ...
    def __ne__(self, other: object, /) -> bool: ...
    def __repr__(self, /) -> str: ...
    def __setstate__(self, state: int, /) -> None: ...
    def __str__(self, /) -> str: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
        ...

    @property
    def value(self) -> int:
        """
        :type: int
        """
        ...
    __members__: dict
    json: logformat
    plain: logformat
    ...

class mat:
    def __add__(self, arg0: mat) -> mat:
        return mat()

    @overload
    def __init__(self) -> None:
        """
        The `mat` object holds a sparse algebriac square matrix. Before creating a `mat` object, ensure that a mesh object is
        available. If a mesh object is not already available, create an empty mesh object. If a mesh object is not available
        before creating a `mat` object, a RuntimeError is raised.

        Examples
        --------
        There are many ways of instantiating an `indexmat` object. There are listed below:

        **Example 1:** `mat(matsize:int, rowaddresses:indexmat, coladdresess:indexmat, vals:densemat)`
        This creates a sparse matrix object of size `matsize`$\\times$`matsize`. The `rowaddresses` and `coladdresess` provide the
        location (row, col) of non-zero values in the sparse matrix. The non-zero values are provided in the dense matrix `vals`.
        Note that a mesh object must already be available before instantiating `mat` object.
        >>> rows = indexmat(7,1, [0,0,1,1,1,2,2])
        >>> cols = indexmat(7,1, [0,1,0,1,2,1,2])
        >>> vals = densemat(7,1, [11,12,13,14,15,16,17])
        >>>
        >>> mymesh = mesh()
        >>> A = mat(3, rows, cols, vals)
        >>> A.print()
        A block 3x3:
        Mat Object: 1 MPI processes
            type: seqaij
        row 0: (0, 11.)  (1, 12.)
        row 1: (0, 13.)  (1, 14.)  (2, 15.)
        row 2: (1, 16.)  (2, 17.)

        **Example 2:** `mat(myformulation:formulation, rowaddresses:indexmat, coladdresses:indexmat, vals:densemat)`
        This creates a sparse matrix object whose `dof` structure is the one in the formulation `projection`. The `rowaddresses` and
        `coladdresess` provide the location (row, col) of non-zero values in the sparse matrix. The non-zero values are provided in the
        dense matrix `vals`.
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>>
        >>> addresses = indexmat(numberofrows=projection.countdofs(), numberofcolumns=1, init=0, step=1)
        >>> vals = densemat(numberofrows=projection.countdofs(), numberofcolumns=1, init=12)
        >>>
        >>> A = mat(formulation=projection, rowaddresses=addresses, coladdresses=addresses, densemat=vals)
        """

    @overload
    def __init__(
        self,
        matsize: int,
        rowaddresses: indexmat,
        coladdresses: indexmat,
        vals: densemat,
    ) -> None: ...
    @overload
    def __init__(
        self,
        myformulation: formulation,
        rowaddresses: indexmat,
        coladdresses: indexmat,
        vals: densemat,
    ) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    @overload
    def __mul__(self, arg0: float) -> mat: ...
    @overload
    def __mul__(self, arg0: mat) -> mat: ...
    @overload
    def __mul__(self, arg0: vec) -> vec: ...
    def __mul__(self, *args, **kwargs) -> Any: ...
    def __neg__(self) -> mat:
        return mat()

    def __pos__(self) -> mat:
        return mat()

    def __rmul__(self, arg0: float) -> mat:
        return mat()

    def __sub__(self, arg0: mat) -> mat:
        return mat()

    def __truediv__(self, arg0: float) -> mat:
        return mat()

    def copy(self) -> mat:
        """
        This creates a full copy of the matrix. Only the values are copied. (E.g: the `mat.reusefactorization` is set back to the default
        *no* reuse.)

        Example
        -------
        >>> A =
        >>> copiedmat = A.copy()
        """
        return mat()

    def countcolumns(self) -> int:
        """
        This counts and returns the number of columns in the matrix.

        Example
        -------
        >>> numcols = A.countcolumns()
        """
        ...

    def countnnz(self) -> int:
        """
        This counts and returns the number of non-zero entries in the matrix $\\boldsymbol{A_a}$ which is the sub-matrix of
        $\\boldsymbol{A}$ with eliminated Dirichlet constraints. Refer `mat.getainds`.

        If the requested information is not available, then -$1$ is returned.

        Example
        -------
        >>> numnnz = A.countnnz()
        """
        ...

    def countrows(self) -> int:
        """
        This counts and returns the number of rows in the matrix.

        Example
        -------
        >>> numrows = A.countrows()
        """
        ...

    def getainds(self) -> indexmat:
        """
        Let us call *dinds*  the set of unknowns that have a Dirichlet constraint and *ainds* the remaining unknowns.
        The `mat` object $\\boldsymbol{A}$ holds sub-matrices $\\boldsymbol{A_a}$ and $\\boldsymbol{A_d}$ such that

        $$
        \\boldsymbol{A} = \\begin{bmatrix} \\boldsymbol{A_a} & \\boldsymbol{A_d}\\\\ \\boldsymbol{0} & \\boldsymbol{1}\\end{bmatrix}
        $$

        where $\\boldsymbol{A_a}$ is a square matrix equal to $\\boldsymbol{A}$ with eliminated Dirichlet constraints.
        $\\boldsymbol{0}$ is an all zero matrix and $\\boldsymbol{1}$ is the square identity matrix of all Dirichlet constraints.
        Matrices $\\boldsymbol{A_a}$ and $\\boldsymbol{A_d}$ are stored with their local indexing. The methods `mat.getainds` and
        `mat.getdinds` gives the global indexing (i.e index in $\\boldsymbol{A}$) of each local index in $\\boldsymbol{A_a}$ and
        $\\boldsymbol{A_d}$.

        Example
        -------
        >>> ainds = A.getainds()

        See Also
        --------
        mat.getdinds
        """
        return indexmat()

    def getdinds(self) -> indexmat:
        """
        This outputs *dinds*.

        Example
        -------
        >>> dinds = A.getdinds()

        See Also
        --------
        mat.getainds
        """
        return indexmat()

    def print(self) -> None:
        """
        This prints the matrix size and values.

        Example
        -------
        >>> A.print()
        """
        ...

    def reusefactorization(self) -> None:
        """
        The matrix factorization will be reused in `allsolve`.
        """
        ...
    ...

class mesh:
    @overload
    def __init__(self) -> None:
        """
        The mesh object holds the finite element mesh of the geometry.

        Examples
        --------
        A mesh object based on a mesh file can be created through the native reader or via the GMSH API.
        To get more information on the physical regions of the mesh, the `verbosity` argument can be
        set to $2$.
        >>> # Creating a mesh object with the native reader:
        >>> mymesh = mesh("disk.msh")
        >>>
        >>> # Creating a mesh object with GMSH API:
        >>> mymesh = mesh("gmsh:disk.msh")

        In the domain decomposition framework, creating a mesh object requires two additional arguments:
        `globalgeometryskin` and `numoverlaplayers`. Furthermore, the mesh is treated as a part of a global
        mesh. Each MPI rank owns only a part of the global mesh and all ranks must perform the call
        collectively. The argument `globalgeometryskin` is the part of the global mesh skin that belongs to
        the current rank. It can only hold elements of dimension one lower than the geometry dimension.
        The global mesh skin cannot intersect itself. The mesh parts are overlapped by the number of
        overlap layers requested. More than one overlap layer cannot be guaranteed everywhere as the overlapping
        is limited to the direct neighbouring domains.
        `mesh(filename:str, globalgeometryskin:int, numoverlaplayers:int, verbosity:int=1)`


        In the above examples, the mesh objects were created based on a mesh file. Similarly, mesh objects can
        be created based on `shape` objects.
        >>> # define physical regions
        >>> faceregionnumber=1; lineregionnumber=2
        >>>
        >>> # define a quadrangle shape object
        >>> quadface = shape("quadrangle", faceregionnumber, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [10,6,10,6])
        >>>
        >>> # get the leftline from the contour of the quad shape object
        >>> contourlines = quadface.getsons()  # returns a list
        >>> leftline = contourlines[3]
        >>> leftline.setphysicalregion(lineregionnumber)
        >>>
        >>> # create mesh object based on the quadrangle shape and its left-side line
        >>> mymesh = mesh([quadface, leftline])
        >>> mymesh.write("quadmesh.msh")

        Creating a mesh object from the shape object can be carried out also in the domain decomposition
        framework using the following syntax:
        `mesh(inputshapes:List[shape], globalgeometryskin:int, numoverlaplayers:int, verbosity:int=1)`


        It is also possible to combine multiple meshes. Elements shared by the input meshes can either be
        merged or not by setting the bool value for argument `mergeduplicates`. For every input mesh, a new
        physical region containing all elements is created. Set verbosity equal to 2 to get information on
        physical regions in the mesh.
        >>> mymesh = mesh("disk.msh")
        >>> mymesh.shift(2,1,0)     # all entities are shifted by x,y,z amount
        >>> mymesh.write("shifted.msh")
        >>>
        >>> mergedmesh = mesh(True, ["disk.msh", "shifted.msh"])
        >>> mergedmesh.write("merged.msh")
        >>>
        >>> mergedmesh = mesh("merged.msh", 2)
        """

    @overload
    def __init__(self, name: str, verbosity: int = 1) -> None: ...
    @overload
    def __init__(
        self,
        name: str,
        globalgeometryskin: int,
        numoverlaplayers: int,
        verbosity: int = 1,
    ) -> None: ...
    @overload
    def __init__(
        self, mergeduplicates: bool, meshfiles: Sequence[str], verbosity: int = 1
    ) -> None: ...
    @overload
    def __init__(self, inputshapes: Sequence[shape], verbosity: int = 1) -> None: ...
    @overload
    def __init__(
        self,
        inputshapes: Sequence[shape],
        globalgeometryskin: int,
        numoverlaplayers: int,
        verbosity: int = 1,
    ) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    def allgetbounds(self) -> list[float]: ...
    def allprintdimensions(self) -> None: ...
    def createboundarylayer(
        self, boundaries: Sequence[int], volumes: Sequence[int], numlayersplits: int
    ) -> None: ...
    def extrude(
        self,
        newphysreg: int,
        newbndphysreg: int,
        bnd: int,
        extrudelens: Sequence[float],
        keepextrusiondata: bool = True,
    ) -> None:
        """
        This extrudes the boundary region `bnd`. After the extrusion process, `newphysreg` will contain the extruded region and
        `newbndphysreg` will contain the extrusion end boundary. the `extrudelens` is a list specifying the size of each layer in the extrusion.
        The length of list determines the number of mesh layers in the extrusion. If -$1$ is given as the extrusion length for each layer, an optimal
        value is automatically calculated.

        Example
        -------
        >>> vol=1; sur=2; top=3; circle=4   # physical regions defined in disk.msh
        >>> volextruded=5; bndextruded=6;   # new physical regions that will be utilized in extrusion
        >>> mymesh = mesh()
        >>>
        >>> # predefine extrusion
        >>> mymesh.extrude(newphysreg = volextruded, newbndphysreg = bndextruded,
        ...                bnd = sur, extrudelens = [0.1,0.05])
        >>>
        >>> # extrusion is performed when the mesh is loaded.
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("diskpml.msh")

        See Also
        --------
        quanscient.getextrusiondata
        """
        ...

    def getbounds(self) -> list[float]: ...
    def getdimension(self) -> int:
        """
        This returns the dimension of the highest dimension element in the mesh 0D, 1D, 2D or 3D.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> dim = mymesh.getdimension()
        >>> dim
        3
        """
        ...

    def getphysicalregionnumbers(self, dim: int = -1) -> list[int]:
        """
        This returns all physical region numbers of a given dimension. Use -$1$ or no argument to get the regions
        of all dimensions.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> allphysregs = mymesh.getphysicalregionnumbers()
        [4, 2, 3, 1]
        """
        ...

    @overload
    def load(self, name: str, verbosity: int = 1) -> None:
        """
        This method allows an empty mesh object to be populated with mesh data. It takes in the same corresponding
        arguments as required in instantiating a mesh object directly. The only difference with direct instantiation
        is that this method requires that an empty mesh object is already created. If this method is called by
        a non-empty mesh object any existing mesh data are lost.

        Examples
        --------
        >>> # Create an empty mesh object
        >>> mymesh = mesh()
        >>>
        >>> # Load a mesh file with the native reader:
        >>> mymesh.load("disk.msh", 2)
        >>>
        >>> # Load a mesh file with GMSH API:
        >>> mymesh = mesh("gmsh:disk.msh", 2)

        Loading a mesh from the shape objects:
        >>> # define physical regions
        >>> faceregionnumber=1; lineregionnumber=2
        >>>
        >>> # define a quadrangle shape object
        >>> quadface = shape("quadrangle", faceregionnumber, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [10,6,10,6])
        >>>
        >>> # get the leftline from the contour of the quad shape object
        >>> contourlines = quadface.getsons()  # returns a list
        >>> leftline = contourlines[3]
        >>> leftline.setphysicalregion(lineregionnumber)
        >>>
        >>> # Load a mesh from the quadrangle shape and its left-side line
        >>> mymesh = mesh()     # creates an empty mesh object
        >>> mymesh.load([quadface, leftline])
        >>> mymesh.write("quadmesh.msh")

        Combing multiple meshes with `load` method
        >>> mymesh = mesh("disk.msh")
        >>> mymesh.shift(2,1,0)     # all entities are shifted by x,y,z amount
        >>> mymesh.write("shifted.msh")
        >>>
        >>> mergedmesh = mesh()
        >>> mergedmesh.load(True, ["disk.msh", "shifted.msh"])
        >>> mergedmesh.write("merged.msh")
        >>>
        >>> mergedmesh = mesh("merged.msh", 2)
        """

    @overload
    def load(
        self,
        name: str,
        globalgeometryskin: int,
        numoverlaplayers: int,
        verbosity: int = 1,
    ) -> None: ...
    @overload
    def load(
        self, mergeduplicates: bool, meshfiles: Sequence[str], verbosity: int = 1
    ) -> None: ...
    @overload
    def load(self, inputshapes: Sequence[shape], verbosity: int = 1) -> None: ...
    @overload
    def load(
        self,
        inputshapes: Sequence[shape],
        globalgeometryskin: int,
        numoverlaplayers: int,
        verbosity: int = 1,
    ) -> None: ...
    def load(self, *args, **kwargs) -> Any: ...
    @overload
    def move(self, physreg: int, u: expressionlike) -> None:
        """
        This moves the whole or part of the mesh object by the x, y and z components of expression u in the x, y and
        z direction.

        Examples
        --------
        >>> vol = 1
        >>> mymesh = mesh("disk.msh")
        >>> x=field("x"); y=field("y")
        >>>
        >>> # Move the whole mesh object
        >>> mymesh.move(array3x1(0,0, sin(x*y)))
        >>> mymesh.write("moved.msh")
        >>>
        >>> # Move only the mesh part on the physical region 'vol'
        >>> mymesh.move(vol, array3x1(0,0, sin(x*y)))
        >>> mymesh.write("moved.msh")
        """

    @overload
    def move(self, u: expressionlike) -> None: ...
    def move(self, *args, **kwargs) -> Any: ...
    @overload
    def partition(self) -> None:
        """
        This requests a DDM partition of the mesh. This is an overloaded function and can be instantiated in several ways.

        **Example 1**: `partition()`

        This automatically partitions a mesh into parts equal to the number of nodes selected in allsolve.
        >>> mymesh = mesh()
        >>> mymesh.partition()
        >>> mymesh.load("disk.msh")

        **Example 2**: `partition(groupsphysregs: List[List[int]], groupsnumranks: List[int])`

        Here the user has the flexibility to group physical regions and also specify the number of ranks into which the grouped
        physical region is partitioned. In the below example, the "*top+middle*" is grouped into one region and is stored in $1$ rank.
        The "*bottom*" region is partitioned into $2$ ranks. If a simulation is run on $n$ ranks, any remaining ungrouped regions will
        be paritioned into $n$-$1$-$2$ ranks.
        >>> top=1; middle=2; bottom=3; other=4;
        >>> mymesh = mesh()
        >>> mymesh.partition([[top, middle], [bottom]], [1, 2])

        In the below example, the "*top*" region will be partitioned into $4$ ranks. The "*middle+bottom*" region is grouped into one
        region and will be partitioned into $3$ ranks. If a simulation is run on 15 ranks, any remaining ungrouped regions will be
        paritioned into $15$-$4$-$3$=$8$ ranks.
        >>> top=1; middle=2; bottom=3; other=4;
        >>> mymesh = mesh()
        >>> mymesh.partition([[top], [middle,bottom]], [4, 3])

        **Example 3**: `partition(numxyzslices: List[int])`

        Here, the mesh will be partitioned such that the bounding box of the mesh is sliced in $x$, $y$ and $z$ direction
        by the respective numbers specified in the `numxyzslices` argument. This argument is list of three integers that
        specifies the number of slices in the $x$, $y$ and $z$ direction respectively.

        If the `numxyzslices=[5, 17, 1]`, then the bounding box of the mesh is sliced into 5 uniform parts in $x$-direction,
        17 uniform parts in $y$-direction and 1 part in $z$-direction. Therefore, in total the mesh will be decomposed
        into $5 \\times 17 \\times 1 = 85$ sub-domains. Consequently, the **Node count** in Allsolve Runtime settings
        which sets the number of computational nodes must be set to 85. In general, the total **Node count** must be equal
        to the product of the number of slices in $x$,
        $y$ and $z$ direction.
        >>> ...
        >>> mymesh = mesh()
        >>> mymesh.partition([5, 17, 1])
        >>> mymesh.load(...)
        """

    @overload
    def partition(
        self, groupsphysregs: Sequence[Sequence[int]], groupsnumranks: Sequence[int]
    ) -> None: ...
    @overload
    def partition(
        self,
        newlayerregion: int,
        newrestregion: int,
        growthstart: Sequence[int],
        numlayers: int,
    ) -> None: ...
    @overload
    def partition(
        self,
        originregs: Sequence[Sequence[int]],
        targetregs: Sequence[Sequence[int]],
        dat1: Sequence[Sequence[float]],
        dat2: Sequence[Sequence[float]],
        numlayers: int,
    ) -> None: ...
    @overload
    def partition(self, numxyzslices: Sequence[int]) -> None: ...
    def partition(self, *args, **kwargs) -> Any: ...
    def removeduplicatednodes(self, flag: bool) -> None: ...
    @overload
    def rotate(self, physreg: int, x: float, y: float, z: float) -> None:
        """
        This rotates the whole or part of the mesh object first by `ax` degrees around x axis followed by `ay` degrees around
        the y-axis and then by `az` degrees around the z-axis.

        Examples
        --------
        >>> vol = 1
        >>> mymesh = mesh("disk.msh")
        >>>
        >>> # rotate the whole mesh object
        >>> mymesh.rotate(20,60,90)
        >>> mymesh.write("rotated.msh")
        >>>
        >>> # rotate only the mesh part on the physical region 'vol'
        >>> mymesh.rotate(vol, 20,60,90)
        >>> mymesh.write("rotated.msh")
        """

    @overload
    def rotate(self, x: float, y: float, z: float) -> None: ...
    def rotate(self, *args, **kwargs) -> Any: ...
    @overload
    def scale(self, physreg: int, x: float, y: float, z: float) -> None:
        """
        This scales the whole or part of the mesh object first by a factor `x`, `y` and `z` respectively in the
        x, y and z direction.

        Examples
        --------
        >>> vol = 1
        >>> mymesh = mesh("disk.msh")
        >>>
        >>> # scale the whole mesh object
        >>> mymesh.scale(0.1,0.2,1.0)
        >>> mymesh.write("scaled.msh")
        >>>
        >>> # scale only the mesh part on the physical region 'vol'
        >>> mymesh.scale(vol, 0.1,0.2,1.0)
        >>> mymesh.write("scaled.msh")
        """

    @overload
    def scale(self, x: float, y: float, z: float) -> None: ...
    def scale(self, *args, **kwargs) -> Any: ...
    @overload
    def selectanynode(self, newphysreg: int, physregtoselectfrom: int) -> None:
        """
        This tells the mesh object to create a new physical region `newphysreg` that contains a single node arbitrarily chosen in the
        region `physregtoselectfrom`. If no region is selected (i.e. if `physregtoexcludefrom` is empty) or if the argument
        `physregtoexcludefrom` is not provided, then the arbitrary node is chosen considering the whole domain. The new region `newphysreg` is
        created when the `mesh.load` method is called on the mesh object.

        Examples
        --------
        **Example 1**: `mesh.selectanynode(newphysreg:int, physregtoselectfrom:int)`
        >>> vol=1; anynode=12
        >>> mymesh = mesh()
        >>> mymesh.selectanynode(anynode, vol])   # a node is chosen from 'vol' region
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("out.msh")

        **Example 2**: `mesh.selectanynode(newphysreg:int)`
        >>> vol=1; anynode=12
        >>> mymesh = mesh()
        >>> mymesh.selectanynode(anynode)      # a node is chosen from the whole domain
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("out.msh")
        """

    @overload
    def selectanynode(self, newphysreg: int) -> None: ...
    def selectanynode(self, *args, **kwargs) -> Any: ...
    @overload
    def selectbox(
        self,
        newphysreg: int,
        physregtobox: int,
        selecteddim: int,
        boxlimit: Sequence[float],
    ) -> None:
        """
        This tells the mesh object to create a new physical region `newphysreg` that contains elements of the region `physregtobox` that
        are in the box delimited by [$x_1$,$x_2$, $y_1$,$y_2$, $z_1$,$z_2$] given in `boxlimit`. If no region is selected (i.e. if
        `physregtobox` is empty) or if the argument `physregtobox` is not provided, then the box region is created
        considering the whole domain.

        The new region `newphysreg` is created when the `mesh.load` method is called on the mesh object. The elements populated in
        the new region `newphysreg` are of dimension `selecteddim`.

        Examples
        --------
        **Example 1**: `mesh.selectbox(newphysreg:int, physregtobox:int, selecteddim:int, boxlimit:List[double])`
        >>> vol=1; boxregion=12
        >>> mymesh = mesh()
        >>> mymesh.selectbox(boxregion, vol, 3, [0,1, 0,1, 0,0.1])   # select box region from the 'vol' region
        >>> mymesh.load("disk.msh")
        >>>
        >>> v=field("h1"); x=field("x"); y=field("y"); z=field("z")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, x*y*z)
        >>> v.write(vol, "v.vtk", 1)
        >>> v.write(boxregion, "vboxregion.vtk", 1)

        **Example 2**: `mesh.selectbox(newphysreg:int, selecteddim:int, boxlimit:List[double])`
        >>> vol=1; boxregion=12
        >>> mymesh = mesh()
        >>> mymesh.selectbox(boxregion, 3, [0,1, 0,1, 0,0.1])      # select box region from the whole domain
        >>> mymesh.load("disk.msh")
        >>>
        >>> v=field("h1"); x=field("x"); y=field("y"); z=field("z")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, x*y*z)
        >>> v.write(vol, "v.vtk", 1)
        >>> v.write(boxregion, "vboxregion.vtk", 1)
        """

    @overload
    def selectbox(
        self, newphysreg: int, selecteddim: int, boxlimit: Sequence[float]
    ) -> None: ...
    def selectbox(self, *args, **kwargs) -> Any: ...
    @overload
    def selectexclusion(
        self,
        newphysreg: int,
        physregtoexcludefrom: int,
        physregstoexclude: Sequence[int],
    ) -> None:
        """
        This tells the mesh object to create a new physical region `newphysreg` that contains the elements of the region `physregtoexcludefrom`
        that are not in `physregtoexclude`. If no region is selected (i.e. if `physregtoexcludefrom` is empty) or if the argument
        `physregtoexcludefrom` is not provided, then the new region is created considering the whole domain. The new region `newphysreg` is
        created when the `mesh.load` method is called on the mesh object.

        Examples
        --------
        **Example 1**: `mesh.selectexclusion(newphysreg:int, physregtoexlcudefrom:int, physregtoexclude:int)`
        >>> vol=1; sur=2; top=3; box=11; excluded=12
        >>> mymesh = mesh()
        >>> mymesh.selectbox(box, vol, 3, [0,2, -2,2, -2,2])
        >>> mymesh.selectexclusion(excluded, vol, [box])   # physregtoexcludefrom = 'vol'
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("out.msh")

        **Example 2**: `mesh.selectexclusion(newphysreg:int, physregtoexclude:int)`
        >>> vol=1; sur=2; top=3; box=11; excluded=12
        >>> mymesh = mesh()
        >>> mymesh.selectbox(box, vol, 3, [0,2, -2,2, -2,2])
        >>> mymesh.selectexclusion(excluded, [box])      # physregtoexcludefrom = whole domain
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("out.msh")
        """

    @overload
    def selectexclusion(
        self, newphysreg: int, physregstoexclude: Sequence[int]
    ) -> None: ...
    def selectexclusion(self, *args, **kwargs) -> Any: ...
    @overload
    def selectlayer(
        self,
        newphysreg: int,
        physregtoselectfrom: int,
        physregtostartgrowth: int,
        numlayers: int,
    ) -> None:
        """
        This tells the mesh object to create a new physical region `newphysreg` that contains the layer of elements of the region `physregtoselectfrom`
        that touches the region `physregtostartgrowth`. If no region is selected (i.e. if `physregtoselectfrom` is empty) or if the argument
        `physregtoselectfrom` is not provided, then the layer region is created considering the whole domain. When multiple layers are requested
        through the argument `numlayers`, they are grown on top of each other. The new region `newphysreg` is created when the `mesh.load` method
        is called on the mesh object.

        Examples
        --------
        **Example 1**: `mesh.selectlayer(newphysreg:int, physregtoselectfrom:int, physregtostartgrowth:int, numlayers:int)`
        >>> vol=1; sur=2; top=3; layerregion=12
        >>> mymesh = mesh()
        >>> mymesh.selectlayer(layerregion, vol, sur, 1)   # select layer region from the 'vol' region
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("out.msh")

        **Example 2**: `mesh.selectlayer(newphysreg:int, physregtostartgrowth:int, numlayers:int)`
        >>> vol=1; sur=2; top=3; layerregion=12
        >>> mymesh = mesh()
        >>> mymesh.selectlayer(layerregion, sur, 1)      # select layer region from the whole domain
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("out.msh")
        """

    @overload
    def selectlayer(
        self, newphysreg: int, physregtostartgrowth: int, numlayers: int
    ) -> None: ...
    def selectlayer(self, *args, **kwargs) -> Any: ...
    def selectperpendicular(
        self,
        newphysreg: int,
        physregtoselectfrom: int,
        perpendiculardirection: Sequence[float],
    ) -> None: ...
    @overload
    def selectskin(self, newphysreg: int, physregtoskin: int) -> None:
        """
        This tells the mesh object to create a new physical region `newphysreg` that contains elements that form the skin of the
        selected physical regions. If no region is selected (i.e. if `physregtoskin` is empty) or if the argument
        `physregtoskin` is not provided, then the skin region is created considering the whole domain.

        The skin region `newphysreg` is created when the `mesh.load` method is called on the mesh object. The dimension of the skin region
        is always one dimension less than that of the physical regions selected. Note that space derivatives or 'hcurl' field
        evaluations on a surface do not usually lead to the same values as a volume evaluation.

        Examples
        --------
        **Example 1**: `mesh.selectskin(newphysreg:int, physregtoskin)`
        >>> vol=1; skin=12
        >>> mymesh = mesh()
        >>> mymesh.selectskin(skin, vol)        # select skin region from the 'vol' region
        >>>
        >>> mymesh.load("disk.msh")
        >>> v=field("h1"); x=field("x"); y=field("y"); z=field("z")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, x*y*z)
        >>> v.write(vol, "v.vtk", 1)
        >>> v.write(skin, "vskin.vtk", 1)

        **Example 2**: `mesh.selectskin(newphysreg:int)`
        >>> vol=1; skin=12
        >>> mymesh = mesh()
        >>> mymesh.selectskin(skin)           # select skin region from the whole domain
        >>>
        >>> mymesh.load("disk.msh")
        >>> v=field("h1"); x=field("x"); y=field("y"); z=field("z")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, x*y*z)
        >>> v.write(vol, "v.vtk", 1)
        >>> v.write(skin, "vskin.vtk", 1)s
        """

    @overload
    def selectskin(self, newphysreg: int) -> None: ...
    def selectskin(self, *args, **kwargs) -> Any: ...
    @overload
    def selectsphere(
        self,
        newphysreg: int,
        physregtosphere: int,
        selecteddim: int,
        centercoords: Sequence[float],
        radius: float,
    ) -> None:
        """
        This tells the mesh object to create a new physical region `newphysreg` that contains elements of the region `physregtosphere` that
        are in the sphere of prescribed radius and of center [$x_c$, $y_c$,$z_c$] as given in `centercoords`. If no region is selected (i.e. if
        `physregtosphere` is empty) or if the argument `physregtosphere` is not provided, then the sphere region is created
        considering the whole domain.

        The new region `newphysreg` is created when the `mesh.load` method is called on the mesh object. The elements populated in
        the new region `newphysreg` are of dimension `selecteddim`.

        Examples
        --------
        **Example 1**: `mesh.selectsphere(newphysreg:int, physregtosphere:int, selecteddim:int, centercoords:List[double], radius:double)`
        >>> vol=1; sphereregion=12
        >>> mymesh = mesh()
        >>> mymesh.selectsphere(sphereregion, vol, 3, [1,0,0], 1)   # select sphere region from the 'vol' region
        >>> mymesh.load("disk.msh")
        >>>
        >>> v=field("h1"); x=field("x"); y=field("y"); z=field("z")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, x*y*z)
        >>> v.write(vol, "v.vtk", 1)
        >>> v.write(sphereregion, "vsphereregion.vtk", 1)

        **Example 2**: `mesh.selectsphere(newphysreg:int, selecteddim:int, centercoords:List[double], radius:double)`
        >>> vol=1; sphereregion=12
        >>> mymesh = mesh()
        >>> ymesh.selectsphere(sphereregion, 3, [1,0,0], 1)      # select sphere region from the whole domain
        >>> mymesh.load("disk.msh")
        >>>
        >>> v=field("h1"); x=field("x"); y=field("y"); z=field("z")
        >>> v.setorder(vol, 1)
        >>> v.setvalue(vol, x*y*z)
        >>> v.write(vol, "v.vtk", 1)
        >>> v.write(sphereregion, "vsphereregion.vtk", 1)
        """

    @overload
    def selectsphere(
        self,
        newphysreg: int,
        selecteddim: int,
        centercoords: Sequence[float],
        radius: float,
    ) -> None: ...
    def selectsphere(self, *args, **kwargs) -> Any: ...
    def setadaptivity(
        self, criterion: expressionlike, lownumsplits: int, highnumsplits: int
    ) -> None:
        """
        Each element in the mesh will be adapted (refined/coarsened) based on the value of a **positive** criterion (h-adaptivity).
        The max range of the criterion is split into a number of intervals equal to the number of refinement levels in the range
        `lownumsplits` and `highnumsplits`. All intervals have the same size. The barycenter value of the criterion on each element
        is considered to select the interval, and therefore the corresponding refinement of each mesh element. As an example, for a
        criterion with the highest value of 900 over the entire domain and a low/high refinement level requested of 1/3 the refinement on
        mesh elements with criterion value in the range 0 to 300, 300 to 600, 600 to 900 will be 1, 2, 3 levels respectively.

        Example
        -------
        >>> all = 1
        >>> q = shape("quadrangle", all, [0,0,0, 1,0,0, 1.2,1,0, 0,1,0], [5,5,5,5])
        >>> mymesh = mesh([q])
        >>> x = field("x"); y = field("y")
        >>> criterion = 1 + sin(10*x)*sin(10*y)
        >>>
        >>> mymesh.setadaptivity(criterion, 0, 5)
        >>>
        >>> for i in range(5):
        ...     criterion.write(all, f"criterion_{100+i}.vtk", 1)
        ...     adapt(1)
        """
        ...

    @overload
    def setcohomologycuts(self, cutregs: Sequence[int]) -> None:
        """
        This makes the mesh object aware of the cohomology cut regions.

        Example
        -------
        >>> mymesh = mesh()
        >>> mymesh.setcohomologycuts([chreg1, chreg2])
        >>> mymesh.load("disk.msh")
        """

    @overload
    def setcohomologycuts(
        self,
        cutregs: Sequence[int],
        closedloopregs: Sequence[Sequence[int]],
        startnoderegs: Sequence[int],
        startdirections: Sequence[Sequence[float]],
    ) -> None: ...
    @overload
    def setcohomologycuts(
        self,
        physregstocut: Sequence[int],
        subdomains: Sequence[int],
        closedloopregs: Sequence[Sequence[int]],
        startnoderegs: Sequence[int],
        startdirections: Sequence[Sequence[float]],
    ) -> None: ...
    def setcohomologycuts(self, *args, **kwargs) -> Any: ...
    def setphysicalregions(
        self,
        dims: Sequence[int],
        nums: Sequence[int],
        geometryentities: Sequence[Sequence[int]],
    ) -> None: ...
    @overload
    def shift(self, physreg: int, x: float, y: float, z: float) -> None:
        """
        This translates the whole or part of the mesh object by x, y and z amount in the x, y and z direction.

        Examples
        --------
        >>> vol = 1
        >>> mymesh = mesh("disk.msh")
        >>> x=field("x"); y=field("y")
        >>>
        >>> # shift/translate the whole mesh object
        >>> mymesh.shift(1.0, 2.0, 3.0)
        >>> mymesh.write("shifted.msh")
        >>>
        >>> # shift/translate only the mesh part on physical region 'vol'
        >>> mymesh.shift(vol, 1.0, 2.0, 3.0)
        >>> mymesh.write("shifted.msh")
        """

    @overload
    def shift(self, x: float, y: float, z: float) -> None: ...
    def shift(self, *args, **kwargs) -> Any: ...
    def split(self, n: int = 1) -> None:
        """
        This splits each element in the mesh `n` times. Element quality is maximized and element curvature is taken into
        account. Each element is split recursively `n` times as follows:
        * point $\\rightarrow$ 1 point
        * line $\\rightarrow$ 2 lines
        * triangle $\\rightarrow$ 4 triangles
        * quadrangle $\\rightarrow$ 4 quadrangles
        * tetrahedron $\\rightarrow$ 8 tetrahedra
        * hexahedron $\\rightarrow$ 8 hexahedra
        * prism $\\rightarrow$ 8 prisms
        * pyramid $\\rightarrow$ 6 pyramids + 4 tetrahedra

        Example
        -------
        >>> mymesh = mesh()
        >>> mymesh.split()
        >>> mymesh.load("disk.msh")
        >>> mymesh.write("splitdisk.msh")
        """
        ...

    def use(self) -> None:
        """
        This allows one to select which mesh to use in case multiple meshes are available. This call invalidates all objects that are
        based on the previously selected mesh for as long as the latter is not selected again.

        Example
        -------
        >>> finemesh = mesh()
        >>> finemesh.split(2)
        >>> finemesh.load("disk.msh")
        >>> coarsemesh = mesh("disk.msh")
        >>> finemesh.use()
        """
        ...

    @overload
    def write(self, physreg: int, name: str) -> None:
        """
        This writes the mesh object to a given input filename.

        Examples
        --------
        >>> # mesh data
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; top=2; sur=3

        If a physical region is passed in the first argument, then only part of the mesh object included in that
        physical region is written:
        >>> mymesh.write(vol, "out.msh")

        If only the file `name` is provided as an argument, then all the physical regions of the mesh are written.
        >>> mymesh.write("out.msh)
        >>> # or equivalently:
        >>> mymesh.write("out1.msh", physregs=[-1], option=1)

        The argument `physregs` is the list of physical regions that will be written if the argument `option=1`.
        If `option=-1` then all the physical regions except the ones in the list `physregs` will be written. The
        default value for `physregs=-1` which is equivalent to considering all the physical regions (the option argument
        is ignored when `physregs=-1`).
        >>> mymesh.write("out2.msh", [-1], 1)       # all physical regions are written
        >>> mymesh.write("out3.msh", [-1], -1)      # all physical region will be written, ignores 'option' argument
        >>> mymesh.write("out4.msh", [1,2], 1)      # physical regions 1 and 2 will be written
        >>> mymesh.write("out5.msh", [1,2], -1)     # all physical regions except 1 and 2 will be written
        """

    @overload
    def write(
        self, name: str, physregs: Sequence[int] = [-1], option: int = 1
    ) -> None: ...
    def write(self, *args, **kwargs) -> Any: ...
    ...

class parameter:
    @overload
    def __add__(self, arg0: parameter) -> expression: ...
    @overload
    def __add__(self, arg0: float) -> expression: ...
    def __add__(self, *args, **kwargs) -> Any: ...
    @overload
    def __init__(self) -> None:
        """
        The parameter object can hold different expression objects on different geometric regions.

        Examples
        --------
        A parameter object can be a scalar. The following creates an empty object.
        >>> mymesh = mesh("disk.msh")
        >>> E = parameter()

        A parameter object can also be a 2D array. The following creates an empty object.
        >>> E = parameter(3,3)  # a 3x3 parameter matrix
        """

    @overload
    def __init__(self, numrows: int, numcols: int) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    @overload
    def __mul__(self, arg0: parameter) -> expression: ...
    @overload
    def __mul__(self, arg0: float) -> expression: ...
    def __mul__(self, *args, **kwargs) -> Any: ...
    def __neg__(self) -> expression:
        return expression()

    def __pos__(self) -> expression:
        return expression()

    def __radd__(self, arg0: float) -> expression:
        return expression()

    def __rmul__(self, arg0: float) -> expression:
        return expression()

    def __rsub__(self, arg0: float) -> expression:
        return expression()

    def __rtruediv__(self, arg0: float) -> expression:
        return expression()

    @overload
    def __sub__(self, arg0: parameter) -> expression: ...
    @overload
    def __sub__(self, arg0: float) -> expression: ...
    def __sub__(self, *args, **kwargs) -> Any: ...
    @overload
    def __truediv__(self, arg0: parameter) -> expression: ...
    @overload
    def __truediv__(self, arg0: float) -> expression: ...
    def __truediv__(self, *args, **kwargs) -> Any: ...
    def addvalue(self, physreg: int, input: expressionlike) -> None:
        """
        This adds the `ìnput` expression to the parameter's existing value on the physical region `physreg`.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> E = parameter()
        >>> E.setvalue(vol, 150e9)
        >>> E.addvalue(vol, 50e9)   # now E holds a value equal to 150e9 + 50e9 = 200e9

        See Also
        --------
        parameter.setvalue
        """
        ...

    @overload
    def allintegrate(self, physreg: int, integrationorder: int) -> float:
        """
        This is a collective MPI operation and hence must be called by all ranks. This integrates a **scalar** parameter
        over a physical region across all the DDM ranks.

        Note that integration is not allowed on a non-scalar parameter.
        Typically `norm` or `comp` functions are used to obtain an equivalent scalar parameter from a non-scalar parameter to allow integration.

        **Example 1: `allintegrate(physreg:int, integrationorder:int)`**

        The integration is performed over the physical region `physreg`. The integration is exact up to the order of
        polynomials specified in the argument `integrationorder`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> p = parameter()
        >>> p.setvalue(vol, 12)
        >>> integralvalue = p.allintegrate(vol, 4)

        For non-scalar parameter, use `norm` or `comp` to get its scalar equivalent before performing integration.
        >>> p = parameter(3,1) # vector parameter with 3 components
        >>> p.setvalue(vol, array3x1(10,20,30))
        >>> normintgr = norm(p).allintegrate(vol, 4)
        >>> compintgr = comp(0,p).allintegrate(vol, 4)

        **Example 2: `allintegrate(physreg:int, meshdeform:expression, integrationorder:int)`**

        Here, the integration is performed on the deformed mesh configuration `meshdeform`.
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> p = parameter()
        >>> p.setvalue(vol, 12)
        >>> integralvalueondeformedmesh = p.allintegrate(vol, u, 4)

        See Also
        --------
        parameter.integrate
        """

    @overload
    def allintegrate(
        self, physreg: int, meshdeform: expressionlike, integrationorder: int
    ) -> float: ...
    def allintegrate(self, *args, **kwargs) -> Any: ...
    @overload
    def allinterpolate(self, physreg: int, xyzcoord: Sequence[float]) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. Its functionality is as described in
        `parameter.interpolate` but considers the physical region partitioned across the DDM ranks. The argument `xyzcoord`
        must be the same for all ranks.

        Note that interpolation is allowed for both scalar and non-scalar parameters.

        **Example 1: `allinterpolate(physreg:int, xyzcoord:List[double])`**

        This interpolates the parameter at a single point whose [x,y,z] coordinate is provided as an argument.
        The flattened interpolated parameter values are returned if the point was found in the elements of the
        physical region `physreg`. If not found an empty list is returned.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x=field("x"); y=field("y"); z=field("z")
        >>> p = parameter()
        >>> p.setvalue(vol, array3x1(x,y,z))
        >>> interpolated = p.allinterpolate(vol, [0.5,0.6,0.05])
        >>> interpolated
        [0.5, 0.6, 0.05]

        **Example 2: `allinterpolate(physreg:int, meshdeform:expression, xyzcoord:List[double])`**

        A parameter can also be interpolated on a deformed mesh by passing its corresponding field.
        >>> ...
        >>> # interpolation on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> interpolated = p.allinterpolate(vol, u, xyzcoord)

        See Also
        --------
        parameter.interpolate
        """

    @overload
    def allinterpolate(
        self, physreg: int, meshdeform: expressionlike, xyzcoord: Sequence[float]
    ) -> list[float]: ...
    def allinterpolate(self, *args, **kwargs) -> Any: ...
    @overload
    def allmax(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. This returns a list with its first element
        containing the maximum value of a parameter computed across all the DDM ranks over a geometric region. The remaining
        elements of the list provide the coordinates at which the maximum value was found. This is an overloaded method.

        **Example 1**: `allmax(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The maximum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate maximum value, but
        at an increased computational cost. The maximum value is exact when the refinement nodes added to the elements correspond to
        the position of maximum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the maximum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> maxdata = p.allmax(vol, 1)
        >>> maxdata[0]
        2.0

        The search of the maximum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [maxvalue, xcoordmax, ycoordmax, zcoordmax] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the maximum value.
        >>> ...
        >>> maxdatainbox = p.allmax(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `allmax(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The maximum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> maxdataondeformedmesh = p.allmax(vol, u, 1)

        See Also
        --------
        parameter.allmin, parameter.min, parameter.max
        """

    @overload
    def allmax(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def allmax(self, *args, **kwargs) -> Any: ...
    @overload
    def allmin(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This is a collective MPI operation and hence must be called by all ranks. This returns a list with its first element
        containing the minimum value of a parameter computed across all the DDM ranks over a geometric region. The remaining
        elements of the list provide the coordinates at which the minimum value was found. This is an overloaded method.

        **Example 1**: `allmin(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The minimum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate minimum value, but
        at an increased computational cost. The minimum value is exact when the refinement nodes added to the elements correspond to
        the position of minimum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the minimum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> mindata = p.allmin(vol, 1)
        >>> mindata[0]
        2.0

        The search of the minimum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [minvalue, xcoordmin, ycoordmin, zcoordmin] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the minimum value.
        >>> ...
        >>> mindatainbox = p.allmin(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `allmin(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The minimum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The minimum location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> mindataondeformedmesh = p.allmin(vol, u, 1)

        See Also
        --------
        parameter.allmax, parameter.max, parameter.min
        """

    @overload
    def allmin(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def allmin(self, *args, **kwargs) -> Any: ...
    @overload
    def alltimeinterpolate(
        self, physreg: int, xyzcoord: Sequence[float], numtimesteps: int
    ) -> list[float]: ...
    @overload
    def alltimeinterpolate(
        self,
        physreg: int,
        meshdeform: expressionlike,
        xyzcoord: Sequence[float],
        numtimesteps: int,
    ) -> list[float]: ...
    def alltimeinterpolate(self, *args, **kwargs) -> Any: ...
    def atbarycenter(self, physreg: int, onefield: field) -> vec:
        """
        This outputs a `vec` object whose structure is based on the field argument `onefield` and which contains the parameter
        evaluated at the barycenter of each **reference** element of physical region `physreg`. The barycenter of the reference element
        might not be identical to the barycenter of the actual element in the mesh (for curved elements, for general quadrangles,
        hexahedra and prisms). The evaluation at barycenter is constant on each mesh element.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x"); f = field("one")
        >>>
        >>> # Evaluating the parameter
        >>> p = parameter()
        >>> p.setvalue(vol, 12*x)
        >>> p.write(vol, "parameter.vtk", 1)
        >>>
        >>>> # Evaluating the same parameter at barycenter
        >>> myvec = p.atbarycenter(vol, f)
        >>> f.setdata(vol, myvec)
        >>> f.write(vol, "barycentervalues.vtk", 1)
        """
        return vec()

    def countcolumns(self) -> int:
        """
        This returns the number of columns in the parameter.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> E = parameter(2,3)
        >>> E.countcolumns()
        3
        """
        ...

    def countrows(self) -> int:
        """
        This returns the number of rows in the parameter.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> E = parameter(2,3)
        >>> E.countrows()
        2
        """
        ...

    @overload
    def integrate(self, physreg: int, integrationorder: int) -> float:
        """
        This integrates a **scalar** parameter over a physical region.

        Note that integration is not allowed on a non-scalar parameter.
        Typically `norm` or `comp` functions are used to obtain an equivalent scalar parameter from a non-scalar parameter to allow integration.

        Be sure to use `parameter.allintegrate` if more than one node (i.e. DDM) is used in the simulation.

        **Example 1: `integrate(physreg:int, integrationorder:int)`**

        The integration is performed over the physical region `physreg`. The integration is exact up to the order of
        polynomials specified in the argument `integrationorder`
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> p = parameter()
        >>> p.setvalue(vol, 12)
        >>> integralvalue = p.integrate(vol, 4)

        For non-scalar parameter, use `norm` or `comp` to get its scalar equivalent before performing integration.
        >>> p = parameter(3,1) # vector parameter with 3 components
        >>> p.setvalue(vol, array3x1(10,20,30))
        >>> normintgr = norm(p).integrate(vol, 4)
        >>> compintgr = comp(0,p).integrate(vol, 4)


        **Example 2: `integrate(physreg:int, meshdeform:expression, integrationorder:int)`**

        Here, the integration is performed on the deformed mesh configuration `meshdeform`.
        >>> # integration on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> p = parameter()
        >>> p.setvalue(vol, 12)
        >>> integralvalueondeformedmesh = p.integrate(vol, u, 4)

        See Also
        --------
        parameter.allintegrate
        """

    @overload
    def integrate(
        self, physreg: int, meshdeform: expressionlike, integrationorder: int
    ) -> float: ...
    def integrate(self, *args, **kwargs) -> Any: ...
    @overload
    def interpolate(self, physreg: int, xyzcoord: Sequence[float]) -> list[float]:
        """
        This interpolates the parameter at a single point whose [x,y,z] coordinate is provided as an argument.
        The flattened interpolated parameter values are returned if the point was found in the elements of the
        physical region `physreg`. If not found an empty list is returned.

        Note that interpolation is allowed for both scalar and non-scalar parameters.

        Be sure to use `parameter.allinterpolate` if more than one node (i.e. DDM) is used in the simulation.

        **Example 1: `interpolate(physreg:int, xyzcoord:List[double])`**

        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x=field("x"); y=field("y"); z=field("z")
        >>> p = parameter()
        >>> p.setvalue(vol, array3x1(x,y,z))
        >>> interpolated = p.interpolate(vol, [0.5,0.6,0.05])
        >>> interpolated
        [0.5, 0.6, 0.05]


        **Example 2: `interpolate(physreg:int, meshdeform:expression, xyzcoord:List[double])`**

        A parameter can also be interpolated on a deformed mesh by passing its corresponding field.
        >>> ...
        >>> # interpolation on the mesh deformed by field 'u'
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> interpolated = p.interpolate(vol, u, xyzcoord)

        See Also
        --------
        parameter.allinterpolate
        """

    @overload
    def interpolate(
        self, physreg: int, meshdeform: expressionlike, xyzcoord: Sequence[float]
    ) -> list[float]: ...
    def interpolate(self, *args, **kwargs) -> Any: ...
    @overload
    def max(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This returns a list with its first element containing the maximum value of a parameter computed over a geometric region.
        The remaining elements of the list provide the coordinates at which the maximum value was found. This is an overloaded
        method.

        **Example 1**: `max(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The maximum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate maximum value, but
        at an increased computational cost. The maximum value is exact when the refinement nodes added to the elements correspond to
        the position of maximum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the maximum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> maxdata = p.max(vol, 1)
        >>> maxdata[0]
        2.0

        The search of the maximum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [maxvalue, xcoordmax, ycoordmax, zcoordmax] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the maximum value.
        >>> ...
        >>> maxdatainbox = p.max(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `max(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The maximum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> maxdataondeformedmesh = p.max(vol, u, 1)

        See Also
        --------
        parameter.min, parameter.allmax, parameter.allmin
        """

    @overload
    def max(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def max(self, *args, **kwargs) -> Any: ...
    @overload
    def min(
        self, physreg: int, refinement: int, xyzrange: Sequence[float] = []
    ) -> list[float]:
        """
        This returns a list with its first element containing the minimum value of a parameter computed over a geometric region.
        The remaining elements of the list provide the coordinates at which the minimum value was found. This is an overloaded
        method.

        **Example 1**: `min(physreg:int, refinement:int, xyzrange:List[double]=[])`

        The minimum value is obtained over the geometric region `physreg` by splitting all elements `refinement` times in each direction.
        Increasing the refinement will thus lead to a more accurate minimum value, but
        at an increased computational cost. The minimum value is exact when the refinement nodes added to the elements correspond to
        the position of minimum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the minimum is always
        exact to machine precision. The default value of `xyzrange` is an empty list.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> x = field("x")
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> mindata = p.min(vol, 1)
        >>> mindata[0]
        2.0

        The search of the minimum value can be restricted to a box delimited by the last argument `xyzrange` whose form is [xboxmin,xboxmax, yboxmin,
        yboxmin, zboxmax, zboxmin]. The output returned is a list of the form [minvalue, xcoordmin, ycoordmin, zcoordmin] or an empty list
        if the physical region argument is empty or is not in the box provided. If the argument defining the box is not provided, then
        the whole geometric region is considered for evaluating the minimum value.
        >>> ...
        >>> mindatainbox = p.min(vol, 5, [-2,0, -2,2, -2,2])


        **Example 2**: `min(physreg:int, meshdeform:expression, refinement:int, xyzrange:List[double]=[])`

        The minimum value can also be evaluated on the geometry deformed by a field (possibly a curved mesh). The location and the
        delimiting box are on the undeformed mesh.
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> u.setorder(vol, 1)
        >>> p = parameter()
        >>> p.setvalue(vol, 2*x)
        >>> mindataondeformedmesh = p.min(vol, u, 1)

        See Also
        --------
        parameter.max, parameter.allmax, parameter.allmin
        """

    @overload
    def min(
        self,
        physreg: int,
        meshdeform: expressionlike,
        refinement: int,
        xyzrange: Sequence[float] = [],
    ) -> list[float]: ...
    def min(self, *args, **kwargs) -> Any: ...
    def print(self) -> None:
        """
        This prints the information on the parameter to the console.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> E = parameter()
        >>> E.setvalue(vol, 150e9)
        >>> E.print()
        """
        ...

    def setvalue(self, physreg: int, input: expressionlike) -> None:
        """
        This sets the `ìnput` expression to the parameter on the physical region `physreg`.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> E = parameter()
        >>> E.setvalue(vol, 150e9)

        See Also
        --------
        parameter.addvalue
        """
        ...

    @overload
    def write(
        self, physreg: int, numfftharms: int, filename: str, lagrangeorder: int
    ) -> None:
        """
        This evaluates a parameter in the physical region `physreg` and writes it to the file `filename`. The
        `lagrangeorder` is the order of interpolation for the evaluation of the parameter.

        Examples
        --------
        >>> # setup
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> u = field("h1xyz")
        >>> v = field("h1", [1,2,3])
        >>> u.setorder(vol, 1)
        >>> v.setorder(vol, 1)
        >>>
        >>> # interpolation order for writing a parameter
        >>> p = parameter()
        >>> p.setvalue(1e8*u)
        >>> p.write(vol, "uorder1.vtk", 1)    # interpolation order is 1
        >>> p.write(vol, "uorder3.vtk", 3)    # interpolation order is 3
        """

    @overload
    def write(
        self,
        physreg: int,
        numfftharms: int,
        meshdeform: expressionlike,
        filename: str,
        lagrangeorder: int,
    ) -> None: ...
    @overload
    def write(
        self, physreg: int, filename: str, lagrangeorder: int, numtimesteps: int = -1
    ) -> None: ...
    @overload
    def write(
        self,
        physreg: int,
        meshdeform: expressionlike,
        filename: str,
        lagrangeorder: int,
        numtimesteps: int = -1,
    ) -> None: ...
    def write(self, *args, **kwargs) -> Any: ...
    ...

class port:
    @overload
    def __add__(self, arg0: port) -> expression: ...
    @overload
    def __add__(self, arg0: float) -> expression: ...
    def __add__(self, *args, **kwargs) -> Any: ...
    @overload
    def __init__(self) -> None:
        """
        The port object represents a scalar lumped quantity.

        Examples
        --------
        A port object with an initial zero value is created as:
        >>> V = port()

        A multi-harmonic port object with an initial zero value can be created by passing a list of harmonic numbers.
        Refer to the multi-harmonic field constructor for the meaning of the harmonic numbers.
        >>> V = port([2,3])
        """

    @overload
    def __init__(self, harmonicnumbers: Sequence[int]) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    @overload
    def __mul__(self, arg0: port) -> expression: ...
    @overload
    def __mul__(self, arg0: float) -> expression: ...
    def __mul__(self, *args, **kwargs) -> Any: ...
    def __neg__(self) -> expression:
        return expression()

    def __pos__(self) -> expression:
        return expression()

    def __radd__(self, arg0: float) -> expression:
        return expression()

    def __rmul__(self, arg0: float) -> expression:
        return expression()

    def __rsub__(self, arg0: float) -> expression:
        return expression()

    def __rtruediv__(self, arg0: float) -> expression:
        return expression()

    @overload
    def __sub__(self, arg0: port) -> expression: ...
    @overload
    def __sub__(self, arg0: float) -> expression: ...
    def __sub__(self, *args, **kwargs) -> Any: ...
    @overload
    def __truediv__(self, arg0: port) -> expression: ...
    @overload
    def __truediv__(self, arg0: float) -> expression: ...
    def __truediv__(self, *args, **kwargs) -> Any: ...
    def cos(self, freqindex: int) -> port:
        """
        This gets a port that is the $sin$ harmonic at `freqindex` times the fundamental frequency in port V.

        Example
        -------
        >>> V = port([1,2,3,4,5])
        >>> Vs = V.cos(0)
        >>> Vs.getharmonics()
        1

        See Also
        --------
        port.sin
        """
        return port()

    def getharmonics(self) -> list[int]:
        """
        This returns the list of harmonics of the port object.

        Example
        -------
        >>> V = port([1,2,3])
        >>> harms = V.getharmonics()
        >>> harms
        [1, 2, 3]
        """
        ...

    def getname(self) -> str:
        """
        This gets the name of the port object.

        Example
        -------
        >>> V = port()
        >>> V.setname("LumpedMass")
        >>> V.getname()
        'LumpedMass'

        See Also
        --------
        port.setname
        """
        ...

    def getvalue(self) -> float:
        """
        This returns the value of the port object.

        Example
        -------
        >>> V = port()
        >>> V.setvalue(-1.2)
        >>> val = V.getvalue()
        >>> val
        -1.2

        See Also
        --------
        port.setvalue
        """
        ...

    @overload
    def harmonic(self, harmonicnumber: int) -> port:
        """
        This returns a port that is the harmonic/list of harmonics of the port object.

        Example
        -------
        >>> V = port([1,2,3])
        >>> V23 = V.harmonic([2,3])
        >>> V23.getharmonics()
        [2, 3]
        """

    @overload
    def harmonic(self, harmonicnumbers: Sequence[int]) -> port: ...
    def harmonic(self, *args, **kwargs) -> Any: ...
    def print(self) -> None:
        """
        This prints the information of the port object.

        Example
        -------
        >>> V = port([2,3])                 # create a multi-harmonic port object
        >>> V.harmonic(2).setvalue(1)       # set the value of 2nd harmonic
        >>> V.harmonic(3).setvalue(0.5)     # set the value of 3rd harmonic
        >>> V.print()
        Port harmonic 2 has value 1
        Port harmonic 3 has value 0.5
        """
        ...

    def setname(self, name: str) -> None:
        """
        This sets the name for the port object.

        Example
        -------
        >>> V = port()
        >>> V.setname("LumpedMass")
        >>> V.print()
        Port LumpedMass has value 0

        See Also
        --------
        port.getname
        """
        ...

    def setvalue(self, portval: float) -> None:
        """
        This sets the value of the port object.

        Examples
        --------
        >>> V = port()
        >>> V.setvalue(10.0)
        >>> V.print()
        Port has value 10

        To set the value of a multi-harmonic port:
        >>> V = port([2,3])                 # create a multi-harmonic port object
        >>> V.harmonic(2).setvalue(1)       # set the value of 2nd harmonic
        >>> V.harmonic(3).setvalue(0.5)     # set the value of 3rd harmonic
        >>> V.print()
        Port harmonic 2 has value 1
        Port harmonic 3 has value 0.5

        See Also
        --------
        port.harmonic, port.getvalue
        """
        ...

    def sin(self, freqindex: int) -> port:
        """
        This gets a port that is the $sin$ harmonic at `freqindex` times the fundamental frequency in port V.

        Example
        -------
        >>> V = port([1,2,3,4,5])
        >>> Vs = V.sin(2)
        >>> Vs.getharmonics()
        4

        See Also
        --------
        port.cos
        """
        return port()
    ...

class preconditioner: ...

class shape:
    @overload
    def __init__(self) -> None:
        """
        The shape objects are meshed geometric entities. The mesh created based on shapes can be written in `.msh` format
        at any time for visualization in GMSH. It might be needed to change the `color` and `visibility` options in the menu
        `Tools > Options > Mesh` of GMSH.

        Examples
        --------
        Depending on the number and type of arguments, different shape objects can be created for different purposes.
        * Creates a shape with the coordinates of all nodes provided as input:
            - Example 2: for points and lines: `myshape = shape(shapename:str, physreg:int, coords:List[double])`
        * Creates a shape based on the coordinates of the corner nodes in the shape
            - Example 3: for lines and arcs: `myshape = shape(shapename:str, physreg:int, coords:List[double], nummeshpts:int)`
            - Example 4: for triangles and quadrangles: `myshape = shape(shapename:str, physreg:int, coords:List[double], nummeshpts:List[int])`
        * Creates a shape based on sub-shapes provided.
            - Example 5: for lines and arcs: `myshape = shape(shapename:str, physreg:int, subshapes:List[shape], nummeshpts:int)`
            - Example 6: for straight-edged triangles and quadrangles: `myshape = shape(shapename:str, physreg:int, subshapes:List[shape], nummeshpts:List[int])`
            - Example 7: for curved triangles and quadrangles. Also, union of several shapes: `myshape = shape(shapename:str, physreg:int, subshapes:List[shape])`
        * Creates a disk shape.
            - Example 8: `myshape = shape(shapename:str, physreg:int, centercoords:List[double], radius:double, nummeshpts:int)`
            - Example 9: `myshape = shape(shapename:str, physreg:int, centerpoint:shape, radius:double, nummeshpts:int)`

        **Example 1:** Creating an empty shape object
        >>> myshape = shape()

        **Example 2:** `myshape = shape(shapename:str, physreg:int, coords:List[double])`.
        This can be used to create a line going through a list of nodes whose x,y,z coordinates are provided.
        A physical region number is also provided to have access to the geometric regions of interest in the finite element simulation.
        >>> linephysicalregion  = 1
        >>> myline = shape("line", linephysicalregion, [0,0,0, 0.5,0.5,0, 1,1,0, 1.5,1,0, 2,1,0])
        >>> mymesh = mesh([myline])
        >>> mymesh.write("meshed.msh")

        If the nodes in the mesh need to be accessed, a point shape object can be created with corresponding nodal coordinates.
        The nodes can then be accessed through the physical region provided.
        >>> pointphysicalregion = 2
        >>> point1_coords = [0,0,0]
        >>> point2_coords = [2,1,0]
        >>> mypoint1 = shape("point", pointphysicalregion, point1_coords)
        >>> mypoint2 = shape("point", pointphysicalregion, point2_coords)
        >>> # Points 1 and 2 are now available in the `pointphysicalregion=2`.
        >>>
        >>> p = field("h1")
        >>> p.setorder(linephysicalregion, 1)
        >>> p.setconstraint(pointphysicalregion, 2) # Dirichlet boundary constraint will be applied on points 1 and 2

        **Example 3:** `myshape = shape(shapename:str, physreg:int, coords:List[double], nummeshpts:int)`
        This can be used to create:
            a straight line between the first (x1,y1,z1) and last point (x2,y2,z2) provided.
            a circular arc between the first (x1,y1,z1) and second point (x2,y2,z2) whose center is the third point (x3,y3,z3).
        The `nummeshpts` argument corresponds to the number of nodes in the meshed shape. At least two nodes are expected.
        >>> linephysicalregion=1; arcphysicalregion=1
        >>> myline = shape("line", linephysicalregion, [0,0,0, 1,-1,1], 10)     # creates a line mesh with 10 nodes
        >>> myarc = shape("arc", arcphysicalregion, [1,0,0, 0,1,0, 0,0,0], 8)   # creates an arc mesh with 8 nodes
        >>> mymesh = mesh([myline, myarc])
        >>> mymesh.write("meshed.msh")

        **Example 4:** `myshape = shape(shapename:str, physreg:int, coords:List[double], nummeshpts:List[int])`
        This can be used to create:
            a straight-edge quadrangle with a full quadrangle structured mesh.
            a straight-edge triangle with s structured mesh made of triangles along the edge linking the second and third node and quadrangles everywhere else.
        >>> quadranglephysicalregion=1; trianglephysicalregion=2
        >>> myquadrangle = shape("quadrangle", quadranglephysicalregion, [0,0,0, 1,0,0, 1,1,0, -0.5,1,0], [12,10,12,10])
        >>> mytriangle = shape("triangle", trianglephysicalregion, [1,0,0, 2,0,0, 1,1,0], [10,10,10])
        >>> mymesh = mesh([myquadrangle, mytriangle])
        >>> mymesh.write("meshed.msh")
        The `coords` argument provides the `x,y,z`coordinates of the corner nodes. E.g. (0,0,0), (1,0,0), (1,1,0) and (-0.5,1,0) for the quadrangle.
        The `nummeshpts` argument specifies the number of nodes to mesh each of the contour lines. At least two nodes are expected for each contour line.
        All contour lines must have the same number of nodes for the triangle shape while for the quadrangle shape the contour lines facing each other
        must have the same number of nodes.

        **Example 5:** `myshape = shape(shapename:str, physreg:int, subshapes:List[shape], nummeshpts:int)`
        This can be used to create the following shapes from the list of subshapes provided:
            a straight line between the first (x1,y1,z1) and last point (x2,y2,z2) provided.
            a circle arc between the first (x1,y1,z1) and second point (x2,y2,z2) whose center is the third point.
        The `nummeshpts` argument corresponds to the number of nodes in the meshed shape.
        >>> # Point subshapes
        >>> point1 = shape("point", -1, [0,0,0])
        >>> point2 = shape("point", -1, [1,0,0])
        >>> point3 = shape("point", -1, [0,1,0])
        >>> point4 = shape("point", -1, [1,-1,1])
        >>>>
        >>> # Creating line and arc shapes from point subshapes
        >>> linephysicalregion=1; arcphysicalregion=2
        >>> myline = shape("line", linephysicalregion, [point1, point4], 10)
        >>> myarc = shape("arc", arcphysicalregion, [point2, point3, point1], 8)
        >>> mymesh = mesh([myline, myarc])
        >>> mymesh.write("meshed.msh")

        **Example 6:** `myshape = shape(shapename:str, physreg:int, subshapes:List[shape], nummeshpts:List[int])`
        This can be used to create the following shapes from the list of subshpaes provided:
            a straight-edge quadrangle with a full quadrangle structured mesh
            a straight-edge triangle with a structured mesh made of triangles along the edge linking the second and third nodes and quadrangles everywhere.
        The `subshapes` argument provides the list of corner point shapes. The `nummeshpts`argument gives the number of nodes to mesh each of the contour lines.
        At least two nodes are expected for each contour line. All contour lines must have the same number of nodes for the triangle shape while for the quadrangle
        shape the contour lines facing each other must have the same number of nodes.
        >>> # Point subshapes
        >>> point1 = shape("point", -1, [0,0,0])
        >>> point2 = shape("point", -1, [1,0,0])
        >>> point3 = shape("point", -1, [1,1,0])
        >>> point4 = shape("point", -1, [0,1,0])
        >>> point5 = shape("point", -1, [2,0,0])
        >>>
        >>> # Creating triangle and quadrangle shape from subshapes of corner points
        >>> quadranglephysicalregion=1; trianglephysicalregion=2
        >>> myquadrangle = shape("quadrangle", quadranglephysicalregion, [point1, point2, point3, point4], [6,8,6,8])
        >>> mytriangle = shape("triangle", trianglephysicalregion, [point2, point5, point3], [8,8,8])
        >>> mymesh = mesh([myquadrangle, mytriangle])
        >>> mymesh.write("meshed.msh")

        **Example 7:** `myshape = shape(shapename:str, physreg:int, subshapes:List[shape])`
        This can be used to create:
            a curved quadrangle with full quadrangle structured mesh.
            a curved triangle with structured mesh made of triangles along the edge linking the second and third nodes and quadrangles everywhere.
            a shape that is the union of several shapes of the same dimension.
        The `subshapes` argument provides the contour shapes (clockwise or anti-clockwise). All contour lines must have the same number of nodes for the triangle shape
        while for quadrangle shape the contour lines facing each other must have the same number of nodes.
        >>> # Creating subshapes
        >>> line1 = shape("line", -1, [-1,-1,0, 1,-1,0], 10)
        >>> arc2 = shape("arc", -1, [1,-1,0, 1,1,0, 0,0,0], 12)
        >>> line3 = shape("line", -1, [1,1,0, -1,1,0], 10)
        >>> line4 = shape("line", -1, [-1,1,0, -1,-1,0], 12)
        >>> line5 = shape("line", -1, [1,-1,0, 3,-1,0], 12)
        >>> arc6 = shape("arc", -1, [3,-1,0, 1,1,0, 1.6,-0.4,0], 12)
        >>>
        >>> quadranglephysicalregion=1; trianglephysicalregion=2; unionphysicalregion=3
        >>> myquadrangle = shape("quadrangle", quadranglephysicalregion, [line1, arc2, line3, line4])
        >>> mytriangle = shape("triangle", trianglephysicalregion,[line5, arc6, arc2])
        >>> myunion = shape("union", unionphysicalregion, [line1, arc2, line3, line4])
        >>>
        >>> mymesh = mesh([myquadrangle, mytriangle, myunion])
        >>> mymesh.write("meshed.msh")

        **Example 8:** `myshape = shape(shapename:str, physreg:int, centercoords:List[double], radius:double, nummeshpts:int)`
        This is used to create a 2D disk with structured mesh centered around `centercoords`. The `nummeshpts`argument
        corresponds to the number of nodes in the contour circle of the disk. Since the disk has a structured mesh, the number of
        mesh nodes must be a multiple of 4. The `radius` argument provides the radius of the disk.
        >>> diskphysicalregion=1
        >>> mydisk = shape("disk", diskphysicalregion, [1,0,0], 2, 40)
        >>> mymesh = mesh([mydisk])
        >>> mymesh.write("meshed.msh")

        **Example 9:** `myshape = shape(shapename:str, physreg:int, centerpoint:shape, radius:double, nummeshpts:int)`
        This is used to create a 2D disk with structured mesh centered around point shape `centerpoint`. The `nummeshpts`
        argument corresponds to the number of nodes in the contour circle of the disk. Since the disk has a structured mesh,
        the number of mesh nodes must be a multiple of 4. The `radius` argument provides the radius of the disk.
        >>> diskphysicalregion=1
        >>> centerpoint = shape("point", -1, [1,0,0])
        >>> mydisk = shape("disk", diskphysicalregion, centerpoint, 2, 40)
        >>> mymesh = mesh([mydisk])
        >>> mymesh.write("meshed.msh")
        """

    @overload
    def __init__(
        self, shapename: str, physreg: int, coords: Sequence[float]
    ) -> None: ...
    @overload
    def __init__(
        self, shapename: str, physreg: int, coords: Sequence[float], nummeshpts: int
    ) -> None: ...
    @overload
    def __init__(
        self,
        shapename: str,
        physreg: int,
        coords: Sequence[float],
        nummeshpts: Sequence[int],
    ) -> None: ...
    @overload
    def __init__(
        self, shapename: str, physreg: int, subshapes: Sequence[shape], nummeshpts: int
    ) -> None: ...
    @overload
    def __init__(
        self,
        shapename: str,
        physreg: int,
        subshapes: Sequence[shape],
        nummeshpts: Sequence[int],
    ) -> None: ...
    @overload
    def __init__(
        self, shapename: str, physreg: int, subshapes: Sequence[shape]
    ) -> None: ...
    @overload
    def __init__(
        self,
        shapename: str,
        physreg: int,
        centercoords: Sequence[float],
        radius: float,
        nummeshpts: int,
    ) -> None: ...
    @overload
    def __init__(
        self,
        shapename: str,
        physreg: int,
        centerpoint: shape,
        radius: float,
        nummeshpts: int,
    ) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    def convertcurvatureorder(self, targetcurvatureorder: int) -> shape:
        return shape()

    def duplicate(self) -> shape:
        """
        This outputs a shape that is a duplicate of the initial shape. All the subshapes are duplicated recursively
        as well but the object equality relations between subshapes are identical between a shape and its duplicate.

        Example
        -------
        >>> myquadrangle = shape("quadrangle", 1, [-1,-1,0, 1,-1,0, 1,1,0, -1,1,0], [6,8,6,8])
        >>> otherquadrangle = myquadrangle.duplicate()

        See Also
        --------
        shape.move, shape.shift, shape.scale, shape.rotate
        """
        return shape()

    @overload
    def extrude(
        self,
        physreg: int,
        height: float,
        numlayers: int,
        extrudedirection: Sequence[float] = [0.0, 0.0, 1.0],
    ) -> shape:
        """
        A given shape is extruded in the direction specified by the unit vector argument `extrudedirection` ($Z$-axis by default) to form a higher dimensional
        shape. The extrude function works for 0D, 1D and 2D shapes. The `physreg` is the physical region to which the extruded shape is set. The argument
        `height` is the height of extrusion in the direction of extrusion. The number of node layers the extruded mesh should contain is specified by
        `numlayers`.

        Examples
        -------
        **Example 1:** `myshape = shape.extrude(physreg:int, height:double, numlayers:int, extrudedirection:List[double])`
        >>> myquadrangle = shape("quadrangle", 1, [-1,-1,0, 1,-1,0, 1,1,0, -1,1,0], [2,2,2,2])
        >>> volumephysicalregion = 100
        >>> myvolume = myquadrangle.extrude(volumephysicalregion, 1.4, 6, [0,0,1])
        >>> mymesh = mesh([myvolume])
        >>> mymesh.write("meshed.msh")

        **Example 2:** `myshape = shape.extrude(physreg:List[int], height:List[double], numlayers:[int], extrudedirection:List[double])`.

        This extends the `extrude` function to multiblock extrusion.
        >>> mytriangle = shape("triangle", 1, [0,0,0, 1,0,0, 0,1,0], [6,6,6])
        >>>
        >>> '''
        >>> Creating multiblock extrusion:
        >>> ---------|----------|----------|-----------
        >>> block    | physreg  |  height  |  numlayers
        >>> ---------|----------|----------|-----------
        >>> Block 1: |    11    |   0.5    |    3
        >>> Block 2: |    12    |   0.3    |    5
        >>> ---------|----------|----------|-----------
        >>> In block 1, the initial shape is extruded to a height of 0.5 and contains 3 node layers and the extruded shape is set to physical region 11.
        >>> In block 2, the initial shape is extruded to a height of 0.3 (starting from height 0.5) and contains 5 node layers and the extruded shape is set to physical region 12.
        >>> '''
        >>> myvolumes = mytriangle.extrude([11,12], [0.5,0.3], [3,5], [0,0,1])    # creates two extruded shapes
        >>> mymesh = mesh(myvolumes)
        >>> mymesh.write("meshed.msh")
        """

    @overload
    def extrude(
        self,
        physreg: Sequence[int],
        height: Sequence[float],
        numlayers: Sequence[int],
        extrudedirection: Sequence[float] = [0.0, 0.0, 1.0],
    ) -> list[shape]: ...
    def extrude(self, *args, **kwargs) -> Any: ...
    def getcoords(self) -> list[float]:
        """
        This returns the coordinates of all nodes in the shape mesh.

        Examples
        --------
        >>> myquadrangle = shape("quadrangle", 555, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [2,2,2,2])
        >>> myquadrangle.getcoords()
        [0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0]
        """
        ...

    def getcurvatureorder(self) -> int:
        """
        This returns the curvature order of a given shape.

        Example
        -------
        >>> q = shape("quadrangle", 1, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [2,2,2,2])
        >>> q.getcurvatureorder()
        1
        """
        ...

    def getdimension(self) -> int:
        """
        This gives the shape dimension (0D, 1D, 2D or 3D).

        Examples
        --------
        >>> mypoint = shape("point", 111, [0,0,0])
        >>> mypoint.getdimension()
        0
        >>>
        >>> myline = shape("line", 222, [0,0,0, 0.5,0.5,0, 1,1,0, 1.5,1,0, 2,1,0])
        >>> myline.getdimension()
        1
        >>>
        >>> myarc = shape("arc", 333, [1,0,0, 0,1,0, 0,0,0], 8)
        >>> myarc.getdimension()
        1
        >>>
        >>> mytriangle = shape("triangle", 444, [1,0,0, 2,0,0, 1,1,0], [10,10,10])
        >>> mytriangle.getdimension()
        2
        >>>
        >>> myquadrangle = shape("quadrangle", 555, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [6,8,6,8])
        >>> myquadrangle.getdimension()
        2
        >>>
        >>> mylines = myquadrangle.getsons()
        >>> mylines[0].getdimension()
        1
        """
        ...

    def getname(self) -> str:
        """
        This returns the name of the shape.

        Examples
        --------
        >>> mypoint = shape("point", 111, [0,0,0])
        >>> mypoint.getname()
        'point'
        >>>
        >>> myline = shape("line", 222, [0,0,0, 0.5,0.5,0, 1,1,0, 1.5,1,0, 2,1,0])
        >>> myline.getname()
        'line'
        >>>
        >>> myarc = shape("arc", 333, [1,0,0, 0,1,0, 0,0,0], 8)
        >>> myarc.getname()
        'arc'
        >>>
        >>> mytriangle = shape("triangle", 444, [1,0,0, 2,0,0, 1,1,0], [10,10,10])
        >>> mytriangle.getname()
        'triangle'
        >>>
        >>> myquadrangle = shape("quadrangle", 555, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [6,8,6,8])
        >>> myquadrangle.getname()
        'quadrangle'
        >>>
        >>> mylines = myquadrangle.getsons()
        >>> mylines[0].getname()
        'line'
        """
        ...

    def getphysicalregion(self) -> int:
        """
        This gives the physical region number for a given shape.
        The physical region is used in the finite element simulation to identify a region.
        The method returns -1 if the physical region was not set, else a corresponding positive integer.

        Examples
        -------
        >>> myquadrangle = shape("quadrangle", 111, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [6,8,6,8])
        >>> mylines = myquadrangle.getsons()
        >>>
        >>> myline1 = mylines[0]
        >>> myline1.setphysicalregion(2)
        >>> myline1.getphysicalregion()
        2
        >>>
        >>> myline2 = mylines[1]
        >>> myline1.getphysicalregion()
        -1

        See Also
        --------
        shape.setphysicalregion, shape.getsons
        """
        ...

    def getsons(self) -> list[shape]:
        """
        This returns a list containing the direct subshapes of the shape object.
        For a quadrangle, its 4 contour lines are returned.
        For a triangle, its 3 contour lines are returned.

        Example
        -------
        >>> myquadrangle = shape("quadrangle", 111, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [6,8,6,8])
        >>> mylines = myquadrangle.getsons()
        >>> for myline in mylines:
        ...     myline.setphysicalregion(2)
        ...
        >>> mymesh = mesh(mylines)
        >>> mymesh.write("meshed.msh")
        """
        ...

    def move(self, u: expressionlike) -> None:
        """
        This moves the shape (and all its subshapes recursively) in the x,y and z direction by a value
        provided in the 3x1 expression array. When moving multiple shapes that share common subshapes,
        ensure that subshapes are not moved multiple times.

        Parameter
        ---------
        u: `expression`
            3x1 array expression that specifies the values by which shape is moved in x,y,z direction

        Example
        -------
        >>> x=field("x"); y=field("y"); z=field("z")
        >>> myquadrangle = shape("quadrangle", 1, [-1,-1,0, 1,-1,0, 1,1,0, -1,1,0], [12,16,12,16])
        >>> myquadrangle.move(array3x1(0,x,sin(x*y)))
        >>> mymesh = mesh([myquadrangle])
        >>> mymesh.write("meshed.msh")

        See Also
        --------
        shape.shift, shape.scale, shape.rotate, shape.duplicate
        """
        ...

    def rotate(self, alphax: float, alphay: float, alphaz: float) -> None:
        """
        This rotates the shape (and all its subshapes recursively) first by `alphax` degrees around the x-axis, then
        `alphay` degrees around the y-axis and finally `alphaz` degrees around the z-axis. When rotating multiple shapes
        that share common subshapes make sure that subshapes are not rotated multiple times.

        Example
        -------
        >>> myquadrangle = shape("quadrangle", 1, [-1,-1,0, 1,-1,0, 1,1,0, -1,1,0], [6,8,6,8])
        >>> myquadrangle.rotate(0,0,45)
        >>> mymesh = mesh([myquadrangle])
        >>> mymesh.write("meshed.msh")

        See Also
        --------
        shape.move, shape.shift, shape.scale, shape.duplicate
        """
        ...

    def scale(self, scalex: float, scaley: float, scalez: float) -> None:
        """
        This scales the shape (and all its subspaces recursively) in the x, y and z directions by a given factor provided
        respectively by `scalex`, `scaley`, and `scalez`. A factor of 1 keeps the shape unchanged. When scaling multiple
        shapes that share common subshapes make sure the subshapes are not scaled multiple times.

        Example
        -------
        >>> myquadrangle = shape("quadrangle", 1, [-1,-1,0, 1,-1,0, 1,1,0, -1,1,0], [6,8,6,8])
        >>> myquadrangle.scale(2,0.5,2)
        >>> mymesh = mesh([myquadrangle])
        >>> mymesh.write("meshed.msh")

        See Also
        --------
        shape.move, shape.shift, shape.rotate, shape.duplicate
        """
        ...

    def setphysicalregion(self, physreg: int) -> None:
        """
        This sets, for a given shape, a physical region number provided by `physreg`. Subshapes are not affected.
        The physical region is used in the finite element simulation to identify a region.

        Example
        -------
        >>> quadphysicalregion=1; linephysicalregion=2
        >>> myquadrangle = shape("quadrangle", quadphysicalregion, [0,0,0, 1,0,0, 1,1,0, 0,1,0], [6,8,6,8])
        >>> myline = myquadrangle.getsons()[0]  # the shape 'myline' is not associated with any physical region yet.
        >>> myline.setphysicalregion(linephysicalregion)
        >>> mymesh = mesh([myquadrangle, myline])
        >>> mymesh.write("meshed.msh")

        See Also
        --------
        shape.getphysicalregion, shape.getsons
        """
        ...

    def shift(self, shiftx: float, shifty: float, shiftz: float) -> None:
        """
        This shifts the shape (and all its subshapes recursively) in the x, y, and z directions by a value provided
        respectively by `shiftx`, `shifty`, and `shiftz`. When shifting multiple shapes that share common subshapes
        make sure the subspaces are not shifted multiple times.

        Example
        -------
        >>> myquadrangle = shape("quadrangle", 1, [-1,-1,0, 1,-1,0, 1,1,0, -1,1,0], [6,8,6,8])
        >>> myquadrangle.shift(1,1,2)
        >>> mymesh = mesh([myquadrangle])
        >>> mymesh.write("meshed.msh")

        See Also
        --------
        shape.move, shape.scale, shape.rotate, shape.duplicate
        """
        ...
    ...

class spanningtree:
    def __init__(self, physregs: Sequence[int]) -> None:
        """
        The spanningtree object holds a spanning tree whose edges go through all nodes in the mesh without forming a loop.
        The `physregs` is the list of physical regions where the spanning tree is first fully grown before being extended everywhere.

        Example
        -------
        A spanning tree object is created by passing the physical regions 'sur' and 'top'. Hence,
        here the tree is first fully grown on face regions 'sur' and 'top' before extending everywhere.
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3;    # physical regions
        >>> spantree = spannintree([sur, top])
        """
        ...

    def countedgesintree(self) -> int:
        """
        This returns the number of edges in the spanning tree.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3;    # physical regions
        >>> spantree = spannintree([sur, top])
        >>> spantree.countedgesintree()
        1859
        """
        ...

    def write(self, filename: str) -> None:
        """
        This writes the tree into a file for visualization. The `filename` is the name of the file to which the data samples are written.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2; top=3;    # physical regions
        >>> spantree = spannintree([sur, top])
        >>> spantree.write("spantree.vtk")
        """
        ...
    ...

class spline:
    @overload
    def __init__(self) -> None:
        """
        The spline object allows single variate interpolation in a discrete data set using cubic (natural) splines. Before creating
        a spline object, ensure that a mesh object is available. If a mesh object is not already available, create an empty mesh object.
        For multivariate data interpolation refer `grid` class.

        Examples
        --------
        Say the data samples are in a text file, with each data separated by "," as shown below:
        >>> 273,5e9,300,4e9,320,2.5e9,340,1e9

        A spline object can then be created by reading the x-y data contained in the text file.
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>> spl1 = spline(filename="measured.txt", delimiter="\\n")

        The x-y data samples can also be provided in two separate lists or tuples. In that case, a spline
        object is created as follows:
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>> temperature = (273, 300, 320, 340)
        >>> youngsmodulus = (5e9, 4e9, 2.5e9, 1e9)
        >>> spl2 = spline(xin=temperature, yin=youngsmodulus)

        Note that the ordering of the samples provided does not matter. Internally they are always sorted in the ascending
        order of $x$ data.
        """

    @overload
    def __init__(
        self, filename: str, delimiter: str = "\n", linear: bool = False
    ) -> None: ...
    @overload
    def __init__(
        self, xin: Sequence[float], yin: Sequence[float], linear: bool = False
    ) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    @overload
    def evalat(self, input: float) -> float:
        """
        This method interpolates at given `input` $x$ point(s) that falls within the original data range provided. For
        interpolation of inputs outside the range $(x_{min}, x_{max})$ of the original data a linear extrapolation is
        performed.

        Examples
        --------
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>>
        >>> temperature = (320, 273, 340, 300)          # original x input
        >>> youngsmodulus = (2.5e9, 5e9, 1e9, 4e9)      # original y input
        >>> spl = spline(temperature, youngsmodulus)
        >>>
        >>> # Example 1:
        >>> spl.evalat(303)
        3808990714.7315855
        >>>
        >>> # Example 2:
        >>> spl.evalat([298,304,275])
        [4115149273.2849374, 3740948813.982522, 4948833248.562754]
        >>>
        >>> # Example 3:
        >>> spl.evalat(250)
        5586964211.402413
        >>>
        >>> # Example 4:
        >>> spl.evalat([290, 310, 400])
        [4488540558.869314, 3297986891.385768, -3372034956.3046227]
        """

    @overload
    def evalat(self, input: Sequence[float]) -> list[float]: ...
    @overload
    def evalat(self, input: densemat) -> densemat: ...
    def evalat(self, *args, **kwargs) -> Any: ...
    def getderivative(self) -> spline:
        """
        This returns the derivative of the spline.

        The spline polynomial $y(x)$ and its derivative $\\frac{dy}{dx}$:
        $$
        y(x) = ax³ + bx² + cx + d
        $$
        $$
        \\frac{dy}{dx} = 3ax² + 2bx + c
        $$

        Example
        -------
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>>
        >>> temperature = (273, 300, 320, 340)
        >>> youngsmodulus = (5e9, 4e9, 2.5e9, 1e9)
        >>>
        >>> spl = spline(temperature, youngsmodulus)
        >>> spl.write("spline_data.txt", 0, ",")
        273,5000000000,300,4000000000,320,2500000000,340,1000000000
        >>>
        >>> dspl = spl.getderivative()
        >>> dspl.write("splinederivative_data.txt", 0, ",")
        273,-25520183.104452766,300,-60070744.902205572,320,-79265501.45651269,340,-72867249.271743655
        """
        return spline()

    def getxmax(self) -> float:
        """
        This returns the maximum value that $x$ input takes in the original data provided.

        Example
        -------
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>>
        >>> temperature = (320, 273, 340, 300)          # original x input
        >>> youngsmodulus = (2.5e9, 5e9, 1e9, 4e9)      # original y input
        >>> spl = spline(temperature, youngsmodulus)
        >>> spl.getxmax()
        340

        See Also
        --------
        spline.getxmin
        """
        ...

    def getxmin(self) -> float:
        """
        This returns the minimum value that $x$ input takes in the original data provided.

        Example
        -------
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>>
        >>> temperature = (320, 273, 340, 300)          # original x input
        >>> youngsmodulus = (2.5e9, 5e9, 1e9, 4e9)      # original y input
        >>> spl = spline(temperature, youngsmodulus)
        >>> spl.getxmin()
        273

        See Also
        --------
        spline.getxmax
        """
        ...

    def set(
        self, xin: Sequence[float], yin: Sequence[float], linear: bool = False
    ) -> None:
        """
        This method defines a spline object based on the x-y data samples provided in two separate lists or tuples.

        Example
        -------
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>> temperature = (273, 300, 320, 340)
        >>> youngsmodulus = (5e9, 4e9, 2.5e9, 1e9)
        >>>
        >>> myspline = spline() # create an empty spline object
        >>> myspline.set(xin=temperature, yin=youngsmodulus)
        """
        ...

    def write(self, filename: str, numsplits: int, delimiter: str = "\n") -> None:
        """
        This writes to file a refined version of the original data samples with $x$ data sorted in ascending order.
        It can be used to visualize the interpolation obtained with cubic splines. The argument `filename` is the name of the
        file to which the data samples are written. The `numsplits` is the number of additional points between two successive
        $x$ input considered for evaluation and subsequent writing. Minimum value of `numsplits` required is $0$. The
        `delimiter` is a string specifying the separation between the output columns in the written file.

        Examples
        --------
        Create a spline object:
        >>> mymesh = mesh()     # if a mesh object is not already available.
        >>>
        >>> temperature = (320, 273, 340, 300)          # original x input
        >>> youngsmodulus = (2.5e9, 5e9, 1e9, 4e9)      # original y input
        >>> spl = spline(temperature, youngsmodulus)

        **Example 1:**
        If `numsplits = 0`, no additional points are considered and the original data samples are written.
        >>> numsplits = 0
        >>> spl.write("spline_data.txt", numsplits, ",")
        273,5000000000,300,4000000000,320,2500000000,340,1000000000

        **Example 2:**
        If `numsplits = 1`, between two successive $x$ inputs, one additional point is considered for evaluation and subsequent writing.
        >>> numsplits = 1
        >>> spl.write("spline_data.txt", numsplits, "\\n")
        273
        5000000000
        286.5
        4616608146.0674152
        300
        4000000000
        310
        3297986891.3857679
        320
        2500000000
        330
        1734004369.5380774
        340
        1000000000

        Similarly, if `numsplits = 2`, between two successive $x$ inputs, two additional points are considered for evaluation and subsequent writing.
        """
        ...
    ...

class universe:
    @staticmethod
    def getmaxnumthreads() -> int: ...
    @staticmethod
    def setmaxnumthreads(mnt: int) -> None: ...
    @staticmethod
    def setmumpscntl(cntl: int, val: float) -> None: ...
    @staticmethod
    def setmumpsicntl(icntl: int, val: int) -> None: ...
    allowcohomologyreuse = False
    allowmortardirectmapping = True
    allowsolveacceleration = True
    allowsolvescalecolumns = True
    allowsolvescalerows = True
    attemptfactorizationreuse = False
    blocksofdofs: Any = []
    cohomologycuts: Any = []
    cohomologyloadfile = "cohomologydata"
    cohomologywritefile = "cohomologydata"
    ddmcoefs: list
    ddmexchangeowneddofs = True
    ddmprintportrelationsscaling = False
    ddmscaleportrelations = True
    distributeddirectsolver = False
    eigensolveshiftangle = 0.1
    epstype = "krylovschur"
    extraintegrationorder = 0
    fouriercroppingthreshold = 1e-14
    gmresmodifiedgramschmidt = False
    gmresreorthogonalize = True
    highestfrequencyofinterest = -1.0
    maxnumthreads = -1
    mindropfactorizationreuse = 10.0
    mortardirectionsearchdistance = -1.0
    mortarsearchmiss = 1e-10
    mortarsearchradius = 1.1
    numericaljacobian = False
    partitionermaximbalance = 1.001
    partitionertype = "recursive"
    peptype = "toar"
    printconditionnumber = False
    quadmaxnumits = 20
    quadrefinement = False
    quadrelrestol = 1e-14
    quadverbosity = 1
    roundoffnoiselevel = 1e-10
    solveaccelerationstats: Any = [0, 0]
    solvertype = "mumps"
    usequadblas = True
    usereducedacousticpml = False
    usereducedelasticpml = True
    writeownedonly = False
    writetobinary = True
    xdtxdtdtx: Any = [[], [], []]
    ...

class vec:
    def __add__(self, arg0: vec) -> vec:
        return vec()

    @overload
    def __init__(self) -> None:
        """
        The `vec` object holds a vector, be it the solution vector of an algebraic problem or its right-hand side.

        Examples
        --------
        **Example 1:** `vec(formul:formulation)`
        This creates an all-zero vector whose structure and size is the one of formulation *projection*.
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> b = vec(projection)

        **Example 2:** `vec(vecsize:int, addresses:indexmat, vals:densemat)`
        This creates a vector with given values at given addresses.
        >>> allinitialize()
        >>> addresses = indexmat(3,1, [0,1,2])
        >>> vals = densemat(3,1, [5,10,20])
        >>>
        >>> b = vec(3, addresses, vals)
        >>> b.print()
        Vec Object: 1 MPI processes
          type: seq
        5.
        10.
        20.
        >>> allfinalize()
        """

    @overload
    def __init__(self, formul: formulation) -> None: ...
    @overload
    def __init__(self, vecsize: int, addresses: indexmat, vals: densemat) -> None: ...
    def __init__(self, *args, **kwargs) -> None: ...
    @overload
    def __mul__(self, arg0: float) -> vec: ...
    @overload
    def __mul__(self, arg0: vec) -> float: ...
    def __mul__(self, *args, **kwargs) -> Any: ...
    def __neg__(self) -> vec:
        return vec()

    def __or__(self, arg0: field) -> vectorfieldselect:
        return vectorfieldselect()

    def __pos__(self) -> vec:
        return vec()

    def __rmul__(self, arg0: float) -> vec:
        return vec()

    def __sub__(self, arg0: vec) -> vec:
        return vec()

    def __truediv__(self, arg0: float) -> vec:
        return vec()

    def abs(self) -> vec:
        """
        Returns a new vector with each element replaced by its absolute value.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)
        >>>
        >>> absvec = sol.abs()
        """
        return vec()

    def copy(self) -> vec:
        """
        This creates a full copy of the vector object.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)
        >>>
        >>> copiedvec = sol.copy()
        """
        return vec()

    def getallvalues(self) -> densemat:
        """
        This gets the values of all the entries of the vector in sequential order. It returns a column matrix with number
        of rows equal to the the vector object size.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2    >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> myvec = vec(projection)                 # creates a zero vector
        >>>
        >>> vals = densemat(myvec.size(),1, 12)
        >>> myvec.setallvalues(vals)                # all the entries now contain a value of 12
        >>>
        >>> vecvals = myvec.getallvalues()

        See Also
        --------
        vec.setvalue, vec.setvalues, vec.setallvalues, vec.getvalue, vec.getvalues
        """
        return densemat()

    @overload
    def getvalue(self, address: int) -> float:
        """
        This gets the value of the vector object at the given `address`. The `address` provides the index at which the entry
        of a vector is requested. It returns a matrix of size $1 \\times 1$.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2    >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> myvec = vec(projection)                 # creates a zero vector
        >>>
        >>> vals = densemat(myvec.size(),1, 12)
        >>> myvec.setallvalues(vals)                # all the entries now contain a value of 12
        >>>
        >>> vecvals = myvec.getvalue(2)

        See Also
        --------
        vec.setvalue, vec.setvalues, vec.setallvalues, vec.getvalues, vec.getallvalues
        """

    @overload
    def getvalue(self, prt: port) -> float: ...
    def getvalue(self, *args, **kwargs) -> Any: ...
    def getvalues(self, addresses: indexmat) -> densemat:
        """
        This gets the values in the vector that are at the indices given in `addresses`. The `addresses` is the  column
        matrix storing the indices at which the entries of a vector are requested. It returns a column matrix with number
        of rows equal to the length of the `addresses`.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2    >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> myvec = vec(projection)                 # creates a zero vector
        >>>
        >>> vals = densemat(myvec.size(),1, 12)
        >>> myvec.setallvalues(vals)                # all the entries now contain a value of 12
        >>>
        >>> addresses = indexmat(myvec.size(),1, 0,1)
        >>> vecvals = myvec.getvalues(addresses)

        See Also
        --------
        vec.setvalue, vec.setvalues, vec.setallvalues, vec.getvalue, vec.getallvalues
        """
        return densemat()

    def load(self, filename: str) -> None:
        """
        This loads the data of a vector object from a file (either `.bin` or `.txt` ASCII format). This only works correctly if the dof
        structure of the calling vector object is the same as that of the vector object from which the file was written to the disk.
        In other words, the same set of formulation contributions must be defined in the same order.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)
        >>> sol.write("vecdata.bin")        # writes the vector data to a file
        >>>
        >>> loadedvec = vec(projection)
        >>> loadedvec.load("vecdata.bin")   # loads the data to the vector object

        See Also
        --------
        vec.write
        """
        ...

    def noautomaticupdate(self) -> None:
        """
        After this call, the vector object will not have its value automatically updated after hp-adaptivity. If the automatic update is
        not needed then this call is recommended to avoid a possibly costly update to the vector values.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)
        >>>
        >>> sol.noautomaticupdate()
        """
        ...

    def norm(self, type: str = "2") -> float:
        """
        This returns the $L1$, $L2$ or $L$-$infinity$ norm of the vector. The `type` argument determines the type of the norm returned:
        * For `type='1'`, $L1$ norm is computed.
        * For `type='2'`, $L2$ norm is computed, which is the default.
        * For `type='infinity'`, $L$-$infinity$ norm is computed.

        If $v_i$ is the $i^{th}$ element in a vector $\\boldsymbol{V}$ of length $n$, the different norms are defined as follows:
        * L1 norm: $ \\| \\boldsymbol{V} \\|_1 = \\sum\\limits_{i=1}^{n} \\left| v_i \\right| $
        * L2 norm: $ \\| \\boldsymbol{V} \\|_2 = \\sqrt{\\sum\\limits_{i=1}^{n} v_i^2} $
        * L-infinity norm: $ \\| \\boldsymbol{V} \\|_\\infty = \\max\\limits_{1 \\leq i \\leq n}{\\left| v_i \\right|} $


        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)
        >>>
        >>> vals = densemat(sol.size(),1, 12)
        >>> sol.setallvalues(vals)                # all the entries now contain a value of 12
        >>>
        >>> sol.norm()
        108.6646

        See Also
        --------
        vec.sum
        """
        ...

    def permute(self, rowpermute: indexmat, invertit: bool = False) -> None:
        """
        This rearranges the vector in the order of indices prescribed in `rowpermute`.
        The inverse permutation is performed if the boolean flag `invertit` is set to True.
        The `rowpermute` describes the mapping or inverse mapping function.

        Example
        -------
        >>> rows = indexmat(6,1, [0,1,2,3,4,5])
        >>> vals = densemat(6,1, [00,10,20,30,40,50])
        >>>
        >>> v = vec(6, rows, vals)
        >>> permuterows = indexmat(6,1, [3,1,4,5,0,2])
        >>> v.permute(permuterows, invertit=False)
        >>> v.print()
        Vec Object: 1 MPI processes
        type: seq
        30.
        10.
        40.
        50.
        0.
        20.
        >>>
        >>> # Inverting the permutation on the above will give back the original order of the vector.
        >>> v = vec(6, rows, vals)
        >>> permuterows = indexmat(6,1, [3,1,4,5,0,2])
        >>> v.permute(permuterows, invertit=True)
        >>> v.print()
        Vec Object: 1 MPI processes
        type: seq
        0.
        10.
        20.
        30.
        40.
        50.
        """
        ...

    def print(self) -> None:
        """
        This prints the values of the vector object.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)
        >>>
        >>> sol.print()
        """
        ...

    def setallvalues(self, valsmat: densemat, op: str = "set") -> None:
        """
        This replaces all the entries in the vector object by the values in `valsmat`. The addresses of `valsmat` are
        assumed to be in sequential order. If `op='set'`, the values are replaced and if `op='add'` the values are instead
        added to existing ones. This method works on all the entries. The `valsmat` is a column matrix storing the values
        that are replaced in or added to the vector object.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2    >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> myvec = vec(projection)                     # creates a zero vector
        >>>
        >>> vals = densemat(myvec.size(),1, 12)
        >>> myvec.setallvalues(vals)

        See Also
        --------
        vec.setvalue, vec.setvalues, vec.getvalue, vec.getvalues, vec.getallvalues
        """
        ...

    @overload
    def setdata(self, physreg: int, myfield: field, op: str = "set") -> None:
        """
        This sets to the vector the data from the fields and ports defined in the formulation.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)   # creates a zero vector
        Replace the vector data with the data from field `myfield` from physical region `physreg`.
        >>> sol.setdata(vol, v);    # populates the vector with the data from the field v

        **Example 2:** `vec.setdata()`
        Replace the vector data with the data from **all** the fields and ports defined in the associated formulation.
        >>> ...
        >>> sol.setdata();
        """

    @overload
    def setdata(self) -> None: ...
    def setdata(self, *args, **kwargs) -> Any: ...
    @overload
    def setvalue(self, address: int, value: float, op: str = "set") -> None:
        """
        This replaces the value in the vector object at the given `address` with the values in `value`. The 'address' provides the index at which
        the entry is replaced by `value`.  If `op='set'`, the value is replaced and if `op='add'` the value is added to the existing one.
        This method works only on a given single entry. The `address` is the index at which the entry of a vector is replaced/added.
        The `value` is the value that is set/added in the vector object.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2    >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> myvec = vec(projection)                     # creates a zero vector
        >>>
        >>> myvec.setvalue(2, 2.32)

        See Also
        --------
        vec.setvalues, vec.setallvalues, vec.getvalue, vec.getvalues, vec.getallvalues
        """

    @overload
    def setvalue(self, prt: port, value: float, op: str = "set") -> None: ...
    def setvalue(self, *args, **kwargs) -> Any: ...
    def setvalues(
        self, addresses: indexmat, valsmat: densemat, op: str = "set"
    ) -> None:
        """
        This replaces the values in the vector object at the given `addresses` with the values in `valsmat`.
        If `op='set'`, the values are replaced and if `op='add'` the values are instead added to existing ones.
        This method works only on entries given in the `addresses`. The `addresses` is a column matrix storing
        the indices at which the entries of a vector are replaced/added. The `valsmat` is a column matrix storing
        the values that are replaced in or added to the vector object.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2    >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> myvec = vec(projection)                     # creates a zero vector
        >>>
        >>> addresses = indexmat(myvec.size(),1, 0,1)
        >>> vals = densemat(myvec.size(),1, 12)
        >>>
        >>> myvec.setvalues(addresses, vals)            # op is the default 'set'. All entries are replaced by value 12.
        >>> myvec.setvalues(addresses, vals, 'set')     # All entries are replaced by value 12.
        >>> myvec.setvalues(addresses, vals, 'add')     # Value 12 is added to all entries.

        See Also
        --------
        vec.setvalue, vec.setallvalues, vec.getvalue, vec.getvalues, vec.getallvalues
        """
        ...

    def size(self) -> int:
        """
        This returns the size of the vector object. If the vector was instantiated from a formulation, then the vector size
        is equal to the number of dofs in that formulation.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> b = vec(projection)
        >>> b.size()
        82
        """
        ...

    def updateconstraints(self) -> None:
        """
        This updates the values of all Dirichlet constraint entries in the vector.

        Example
        -------
        >>> mymesh = mesh("disk.msh")
        >>> vol=1; sur=2
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>>
        >>> b = vec(projection)
        >>>
        >>> v.setconstraint(sur, 1)
        >>> b.updateconstraints()
        """
        ...

    def write(self, filename: str) -> None:
        """
        This writes all the data in the vector object to disk in a lossless and compact form. The file can be written in binary `.bin`
        format (extremely compact but less portable) or in ASCII `.txt` format (portable). The `filename` is the name of the file to
        which the data from the vector object is written.

        Examples
        --------
        >>> mymesh = mesh("disk.msh")
        >>> vol = 1
        >>> v = field("h1")
        >>> v.setorder(vol, 1)
        >>> projection = formulation()
        >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
        >>> sol = vec(projection)
        >>>
        >>> sol.write("vecdata.txt")    # writes the vector data to a file

        See Also
        --------
        vec.load
        """
        ...
    ...

class vectorfieldselect:
    def setdata(self, physreg: int, myfield: field, op: str = "set") -> None: ...
    ...

class wallclock:
    def __init__(self) -> None:
        """
        This initializes the wall clock object.
        """
        ...

    def pause(self) -> None:
        """
        This pauses the clock. The `wallclock.pause` and `wallclock.resume` functions allow to time selected operations in loop.

        Example
        -------
        >>> myclock = wallclock()
        >>> myclock.pause()
        >>> # Do something
        >>> myclock.resume()
        >>> myclock.print()

        See Also
        --------
        wallclock.resume
        """
        ...

    def print(self, toprint: str = "") -> None:
        """
        This prints the time elapsed in the most appropriate format ($ns$, $\\mu s$, $ms$ or $s$).
        It also prints the message passed in the argument `toprint` (if any).

        Example
        -------
        >>> myclock = wallclock()
        >>> myclock.print("Time elapsed")   # or myclock.print()
        """
        ...

    def resume(self) -> None:
        """
        This resumes the clock. The `wallclock.pause` and `wallclock.resume` functions allow to time selected operations in loop.

        Example
        -------
        >>> myclock = wallclock()
        >>> myclock.pause()
        >>>
        >>> for i in range (0, 10):
        >>>     myclock.resume()
        >>>     # Do something and time it
        >>>     myclock.pause()
        >>>     # Do something else
        >>> myclock.print()

        See Also
        --------
        wallclock.pause
        """
        ...

    def tic(self) -> None:
        """
        This resets the clock.

        Example
        -------
        >>> myclock = wallclock()
        >>> myclock.tic()

        See Also
        --------
        wallclock.toc
        """
        ...

    def toc(self) -> float:
        """
        This returns the time elapsed (in $ns$).

        Example
        -------
        >>> myclock = wallclock()
        >>> timeelapsed = myclock.toc()

        See Also
        --------
        wallclock.tic
        """
        ...
    ...

def EnutoH(E: expressionlike, nu: expressionlike) -> expression:
    """
    Given the material properties Young's modulus $E$ and Poisson's ratio $\\nu$, this functions creates a $6 \\times 6$ elasticity 
    tensor $H$ for an isoptropic material.

    $$
    \\boldsymbol{H} = \\frac{E}{(1+\\nu)(1-2\\nu)} 
                      \\begin{bmatrix} 
                        1-\\nu & \\nu   & \\nu   & 0                   & 0                   & 0 \\\\
                        \\nu   & 1-\\nu & \\nu   & 0                   & 0                   & 0 \\\\
                        \\nu   & \\nu   & 1-\\nu & 0                   & 0                   & 0 \\\\
                        0      & 0      & 0      & \\dfrac{1-2\\nu}{2} & 0                   & 0 \\\\
                        0      & 0      & 0      & 0                   & \\dfrac{1-2\\nu}{2} & 0 \\\\
                        0      & 0      & 0      & 0                   & 0                   & \\dfrac{1-2\\nu}{2}
                      \\end{bmatrix}
    $$

    The $6 \\times 6$ elasticity tensor defines the relation between the stress and strain components in Voigt notation
    ($\\boldsymbol{\\sigma} = \\boldsymbol{H} \\boldsymbol{\\varepsilon}$).

    In Voigt notation,
    - the stress components are written as $(\\sigma_{xx},\\sigma_{yy},\\sigma_{zz},\\sigma_{yz},\\sigma_{xz},\\sigma_{xy})$.
    - the strain components are written as $(\\varepsilon_{xx},\\varepsilon_{yy},\\varepsilon_{zz},\\gamma_{yz},\\gamma_{xz},\\gamma_{xy})$.

    Note that the shear strain components in Voigt notation are twice the tensorial shear strain.

    Example
    -------
    >>> ...
    >>> E = 160e9
    >>> nu = 0.34
    >>> H = EnutoH(E, nu)
    >>> ...
    >>> form += integral(solidregion, predefinedelasticity(dof(u), tf(u), H))

    See Also
    --------
    Htoplanestrain, Htoplanestress, predefinedelasticity
    """
    return expression()

def Htoplanestrain(H: expressionlike) -> expression:
    """
    This function transforms a 3D elasticity tensor $H$ of size $6 \\times 6$ to a 2D tensor of size $3 \\times 3$ in accordance 
    to the plane strain assumption.

    In Voigt notation, the general 3D stress-strain relation ($\\boldsymbol{\\sigma} = \\boldsymbol{H} \\boldsymbol{\\varepsilon}$) is written as     
    $$
        \\begin{bmatrix}
            \\sigma_{xx}\\\\
            \\sigma_{yy}\\\\
            \\sigma_{zz}\\\\
            \\sigma_{yz}\\\\
            \\sigma_{xz}\\\\
            \\sigma_{xy}
        \\end{bmatrix} 
        = 
        \\begin{bmatrix}
            H_{00} & H_{01} & H_{02} & H_{03} & H_{04} & H_{05}\\\\
            H_{10} & H_{11} & H_{12} & H_{13} & H_{14} & H_{15}\\\\
            H_{20} & H_{21} & H_{22} & H_{23} & H_{24} & H_{25}\\\\
            H_{30} & H_{31} & H_{32} & H_{33} & H_{34} & H_{35}\\\\
            H_{40} & H_{41} & H_{42} & H_{43} & H_{44} & H_{45}\\\\
            H_{50} & H_{51} & H_{52} & H_{53} & H_{54} & H_{55}
        \\end{bmatrix}
        \\begin{bmatrix}
            \\varepsilon_{xx}\\\\
            \\varepsilon_{yy}\\\\
            \\varepsilon_{zz}\\\\
            \\gamma_{yz}\\\\
            \\gamma_{xz}\\\\
            \\gamma_{xy}
        \\end{bmatrix}
    $$

    Plane strain assumption is valid for solid bodies experiencing in-plane (typically XY plane) loading and having a relatively 
    large dimension in the out-of-plane direction (typically Z-direction). Under this assumption, the strains in Z-direction 
    are zero:
    $$
        \\varepsilon_{zz} = \\gamma_{yz} = \\gamma_{xz} = 0 
    $$

    Consequently, the in-plane stress components are decoupled from the out-of-plane strains and only depend on the in-plane strains.
    $$
        \\begin{bmatrix}
            \\sigma_{xx}\\\\
            \\sigma_{yy}\\\\
            \\sigma_{xy}
        \\end{bmatrix} 
        = 
        \\begin{bmatrix}
            H_{00} & H_{01} & H_{05}\\\\
            H_{10} & H_{11} & H_{15}\\\\
            H_{50} & H_{51} & H_{55}
        \\end{bmatrix}
        \\begin{bmatrix}
            \\varepsilon_{xx}\\\\
            \\varepsilon_{yy}\\\\
            \\gamma_{xy}
        \\end{bmatrix}
    $$

    Example
    -------
    >>> ...
    >>> # It is enough to only provide the lower triangular part of the elasticity matrix as it is symmetric
    >>> H = expression(6,6, [195e9, 36e9,195e9, 64e9,64e9,166e9, 0,0,0,80e9, 0,0,0,0,80e9, 0,0,0,0,0,51e9])
    >>>
    >>> # Transform the 6x6 elasticity matrix to 3x3 with plane strain assumption
    >>> H2d = planestrain(H)
    >>> ...
    >>> form += integral(solidregion, predefinedelasticity(dof(u), tf(u), H2d))

    See Also
    --------
    Htoplanestress, EnutoH, predefinedelasticity
    """
    return expression()

def Htoplanestress(H: expressionlike) -> expression:
    """
    This function transforms a 3D elasticity tensor $H$ of size $6 \\times 6$ to a 2D tensor of size $3 \\times 3$ in accordance
    to the plane stress assumption.

    Plane stress assumption is valid on very thin plates where the stress components in out-of-plane direction are zero:
    $$
        \\sigma_{zz} = \\sigma_{yz} = \\sigma_{xz} = 0
    $$

    Example
    -------
    >>> ...
    >>> # It is enough to only provide the lower triangular part of the elasticity matrix as it is symmetric
    >>> H = expression(6,6, [195e9, 36e9,195e9, 64e9,64e9,166e9, 0,0,0,80e9, 0,0,0,0,80e9, 0,0,0,0,0,51e9])
    >>>
    >>> # Transform the 6x6 elasticity matrix to 3x3 with plane stress assumption
    >>> H2d = planestress(H)
    >>> ...
    >>> form += integral(solidregion, predefinedelasticity(dof(u), tf(u), H2d))

    See Also
    --------
    Htoplanestrain, EnutoH, predefinedelasticity
    """
    return expression()

def abort(exitcode: int) -> None:
    """
    <<INTERNAL>>
    Calls MPI_Abort with the provided exit code.

    Example
    -------
    >>> import quanscient as qs
    >>> qs.abort(1)
    """
    ...

def abs(input: expressionlike) -> expression:
    """
    This returns an expression that is the absolute value of the input expression.

    Example
    -------
    >>> expr = abs(-2.5)
    >>> expr.print();
    Expression size is 1x1
     @ row 0, col 0 :
    2.5
    """
    return expression()

def absZ(V: expressionlike, I: expressionlike) -> float:
    """
    This returns an expression that is the magnitude of the Z = V/I complex impedance.

    See Also
    --------
    realZ, imagZ, argZ
    """
    ...

def acos(input: expressionlike) -> expression:
    """
    This returns an expression that is the $arccos$ or $cos^{-1}$ of input. The output expression is in `radians`.

    Example
    -------
    >>> expr = acos(0)
    >>> expr.print();                    # in radians
    Expression size is 1x1
     @ row 0, col 0 :
    1.5708
    >>>
    >>> (expr * 180/getpi()).print();    # in degrees
    Expression size is 1x1
     @ row 0, col 0 :
    90

    See Also
    --------
    sin, cos, tan, asin, atan
    """
    return expression()

def adapt(verbosity: int = 0) -> bool:
    """
    This function is used to perform a h/p/hp adaptation according to the defined h/p/hp adaptivity settings. To define the
    h-adaptivity use function `mesh.setadaptivity`. To define a p-adaptivity for a field use function `field.setorder`.

    The function returns True if the mesh or any field order was changed by the adaption and returns False if no changes were
    made.

    Example
    -------
    >>> all = 1
    >>> q = shape("quadrangle", all, [0,0,0, 1,0,0, 1.2,1,0, 0,1,0], [5,5,5,5])
    >>> mymesh = mesh([q])
    >>> x = field("x"); y = field("y")
    >>> criterion = 1 + sin(10*x)*sin(10*y)
    >>>
    >>> mymesh.setadaptivity(criterion, 0, 5)
    >>>
    >>> for i in range(5):
    ...     criterion.write(all, f"criterion_{100+i}.vtk", 1)
    ...     adapt(1)

    See Also
    --------
    mesh.setadaptivity, field.setorder, alladapt
    """
    ...

def aggregatetime(io: iodata, aggregationop: str, dataop: str) -> iodata:
    return iodata()

def alladapt(verbosity: int = 0) -> bool:
    """
    This is a collective MPI operation and hence must be called by all ranks. It replaces the `adapt` function in the DDM
    framework. This function is used to perform a h/p/hp adaptation according to the defined h/p/hp adaptivity settings. To define the
    h-adaptivity use function `mesh.setadaptivity`. To define a p-adaptivity for a field use function `field.setorder`.

    Example
    -------
    >>> ...
    >>> alladapt()

    See Also
    --------
    adapt
    """
    ...

def allaverage(physreg: int, expr: expressionlike, integrationorder: int) -> float:
    """
    This functions returns the average value of a scalar expression `expr` over a given physical region `physreg`.
    This is equivalent to `qs.allintegrate(physreg, expr, integrationorder)/qs.allintegrate(physreg, 1, integrationorder)`.
    The argument `integrationorder` determines the order of the integration rule used to compute the integral.

    Example
    -------
    >>> # Value output: pressure average
    >>> var.discrete = qs.allaverage(reg.water_top, fld.p, 2)
    >>> qs.setoutputvalue("pressure average", var.discrete, qs.gettime())

    See Also
    --------
    allinterpolate, allprobe, allintegrate
    """
    ...

def allcomputeacousticradiationpattern(
    form: formulation,
    skinregion: int,
    region: int,
    p: field,
    cfar: float,
    rhofar: float,
    numelems: int,
    planenormal: Sequence[float] = [],
    indB: bool = True,
    fittogeo: bool = True,
) -> iodata:
    return iodata()

def allcomputecapacitances(
    sols: Sequence[vec], primals: Sequence[port]
) -> list[float]: ...
def allcomputeemradiationpattern(
    form: formulation,
    skinregion: int,
    region: int,
    E: field,
    mufar: float,
    epsilonfar: float,
    numelems: int,
    planenormal: Sequence[float] = [],
    indB: bool = True,
    fittogeo: bool = True,
) -> iodata:
    return iodata()

@overload
def allcomputesparameters(
    portsphysregs: Sequence[int],
    E: field,
    Esources: Sequence[expressionlike],
    Esols: Sequence[vec],
    integrationorder: int = 5,
) -> list[list[float]]:
    """
    This function extracts the S-parameters $S_{ij}$ corresponding to the physical regions `portphysregs` from the solution list `sols`.
    The parameters `sources` and `modeprojects` should contain what was used as `drivesignal` and `lumpfield` with modedrive function.
    The function returns two lists that contain the real and imaginary parts of the S-parameters in row-major order ($S_{11}, S_{12}, \\ldots$), respectively.

    For the definition of S-parameters, we assume that the input signal at port $i$ is a complex number $a_i$ times the reference mode of port $i$.
    If port $i$ is driven, $a_i$ is the driving signal used for feeding; otherwise $a_i=0$.
    The output signal at port $i$ is a complex number $b_i$ times the reference mode of port $i$.
    The S-parameter $S_{ij}$ is defined such that the equation $S_{ij}=b_i/a_j$ holds when port $j$ is driven and the others are not.

    Example
    -------
    >>> # Suppose a mesh has been loaded with physical regions (port1, port2, waveguide, pec_boundary) and E, mur, epsr_real, and eps_imag have been defined so that the following calls make sense:
    >>> port1mode0 = qs.alleigenport(port1, 1, 0, 1000, E, mur * qs.getmu0(), 0, epsr_real * qs.getepsilon0(), epsr_imag * qs.getepsilon0(), 0, 0, [0.0, 0.0, 1.0], 1e-06, 1000)[0]
    >>> port2mode0 = qs.alleigenport(port2, 1, 0, 1000, E, mur * qs.getmu0(), 0, epsr_real * qs.getepsilon0(), epsr_imag * qs.getepsilon0(), 0, 0, [0.0, 0.0, -1.0], 1e-06, 1000)[0]
    >>>
    >>> form = qs.formulation()
    >>>
    >>> # Prepare the lumpfield constraints:
    >>> lumpfields = form.lump([port1, port2], [2, 3])
    >>>
    >>> # Electromagnetic waves
    >>> form += qs.integral(waveguide, 3, qs.predefinedemwave(qs.dof(E), qs.tf(E), mur * qs.getmu0(), 0, epsr_real * qs.getepsilon0(), epsr_imag * qs.getepsilon0(), 0, 0, "oo2"))
    >>>
    >>> # Drive and absorb the mode of port1 (feeding term in block number 1):
    >>> form += qs.modedrive(port1, qs.sn(1), E, port1mode0[0], port1mode0[1], port1mode0[4], port1mode0[5], [0.0, 0.0, 1.0], lumpfields[0], 1)
    >>>
    >>> # Drive and absorb the mode of port2 (feeding term in block number 2):
    >>> form += qs.modedrive(port2, qs.sn(1), E, port2mode0[0], port2mode0[1], port2mode0[4], port2mode0[5], [0.0, 0.0, -1.0], lumpfields[1], 2)
    >>>
    >>> sols = form.allsolve(relrestol=1e-06, maxnumit=1000, nltol=1e-05, maxnumnlit=-1, relaxvalue=-1, rhsblocks=[[0, 1], [0, 2]])
    >>>
    >>> sparams = qs.allcomputesparameters([port1, port2], [qs.sn(1), qs.sn(1)], sols, lumpfields)

    See Also
    --------
    alleigenport, modedrive, formulation.allsolve, formulation.lump, printsparameters
    """

@overload
def allcomputesparameters(
    portsphysregs: Sequence[int],
    sources: Sequence[expressionlike],
    sols: Sequence[vec],
    modeprojects: Sequence[field],
) -> list[list[float]]: ...
@overload
def allcomputesparameters(
    portsphysregs: Sequence[int],
    sources: Sequence[expressionlike],
    sols: Sequence[vec],
    modeprojectsorprimals: Sequence[expressionlike],
    Rrefs: Sequence[float],
) -> list[list[float]]: ...
def allcomputesparameters(*args, **kwargs) -> Any: ...
def alldirection(
    vol: int, faceorig: int, facedest: int, verbosity: int = 1
) -> expression:
    """
    <<INTERNAL>>
    """
    return expression()

@overload
def alleigenport(
    portphysreg: int,
    numeigenvalues: int,
    targetbeta: float,
    E: field,
    mu: expressionlike,
    eps: expressionlike,
    portnormal: Sequence[float],
    ddmrelrestol: float = -1.0,
    ddmmaxnumit: int = -1,
    drivingfrequency: float = -1.0,
    eigentol: float = 1e-06,
    eigenmaxnumits: int = 1000,
    integrationorder: int = 5,
    verbosity: int = 1,
) -> list[list[expression]]:
    """
    This function computes the eigenmodes of a waveguide whose cross section $S$ is the given physical region `portphysreg`.
    The material parameters $\\mu$, $\\epsilon$, and $\\sigma$ are required as input arguments; these can be anisotropic, and both real and imaginary parts should be given.
    The surface normal `portnormal` is assumed to point in the direction of propagation.
    The boundary condition (PEC) and the approximation order is extracted from the input field `E`.

    For each found mode, the function returns the real and imaginary parts of the transverse and longitudal components of the fields $E$ and $H$ and the propagation constant $\\gamma=\\alpha+j\\beta$ as a list of expressions.
    The returned modes are scaled such that the power into the waveguide,
    $$
    P = \\frac12\\int_{S}\\textup{Re}(E\\times H^{*})\\cdot \\textup{d}S,
    $$
    equals one watt; `integrationorder` determines the order of the integration rule used to compute this integral.

    By default, the function throws an error if material parameters are anisotropic in the direction of propagation.
    This is because the computed modes can not be used with modedrive function in that case.
    To compute the modes anyway, the error check can be disabled by setting `errorifzanisotropic = false`.

    Evanescent modes are filtered according to `evanescentfiltertol` so that modes are accepted only if the imaginary part of the eigenvalue is greater than the given tolerance times the real part.

    Example
    -------
    >>> # Load a mesh with physical regions:
    >>> wg1_crosssection = 9; wg2_crossection = 10;
    >>> portphysreg = 11; full_waveguide = 12;
    >>> portboundary = 13; skin = 14;
    >>> mymesh = qs.mesh()
    >>> mymesh.selectskin(portboundary, portphysreg)
    >>> mymesh.selectskin(skin)
    >>> mymesh.partition()
    >>> mymesh.load("gmsh:waveguide.msh", skin, 1, 1)
    >>>
    >>> # Set input parameter values:
    >>> E = qs.field("hcurl")
    >>> E.setorder(full_waveguide, 2)
    >>> E.setconstraint(portboundary)
    >>> epsr = qs.parameter(); mur = qs.parameter();
    >>> epsr.setvalue(wg1_crosssection, 2.25)
    >>> epsr.setvalue(wg2_crossection, 1.0)
    >>> mur.setvalue(portphysreg, 1.0);
    >>>
    >>> # Attempt to find 4 modes, targetting the eigenvalue 3e6 * i:
    >>> modes = qs.alleigenport(portphysreg, 4, 0, 3e6, E, mur * qs.getmu0(), 0.0, epsr * qs.getepsilon0(), 0.0, 0.0, 0.0, [0.0, 0.0, 1.0], 1e-6, 100, 1.4314e14, 1e-8)
    >>>
    >>> for i in range(len(modes)):
    >>>     # The fields are returned in the following order:
    >>>     modes[i][0].write(portphysreg, 'Etreal_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     modes[i][1].write(portphysreg, 'Etimag_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     modes[i][2].write(portphysreg, 'Elreal_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     modes[i][3].write(portphysreg, 'Elimag_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     modes[i][4].write(portphysreg, 'Htreal_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     modes[i][5].write(portphysreg, 'Htimag_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     modes[i][6].write(portphysreg, 'Hlreal_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     modes[i][7].write(portphysreg, 'Hlimag_rank' + str(qs.getrank()) + '_mode' + str(i) + '.vtu', 2)
    >>>     # Evaluate the eigenvalue expression to access the value:
    >>>     if (qs.getrank() == 0):
    >>>         alpha = modes[i][8].evaluate()
    >>>         beta = modes[i][9].evaluate()
    >>>         print('Mode ' + str(i) + ' has eigenvalue ' + str(alpha) + ' + ' + str(beta) + ' * i.')

    See Also
    --------
    modedrive, rectangularport
    """

@overload
def alleigenport(
    portphysreg: int,
    numeigenvalues: int,
    targetreal: float,
    targetimag: float,
    E: field,
    mu_real: expressionlike,
    mu_imag: expressionlike,
    eps_real: expressionlike,
    eps_imag: expressionlike,
    sigma_real: expressionlike,
    sigma_imag: expressionlike,
    portnormal: Sequence[float],
    ddmrelrestol: float = -1.0,
    ddmmaxnumit: int = -1,
    drivingfrequency: float = -1.0,
    eigentol: float = 1e-06,
    eigenmaxnumits: int = 1000,
    integrationorder: int = 5,
    verbosity: int = 1,
    errorifzanisotropic: bool = True,
    evanescentfiltertol: float = 0.0,
) -> list[list[expression]]: ...
def alleigenport(*args, **kwargs) -> Any: ...
@overload
def allextrapolateacousticfield(
    form: formulation,
    skinregion: int,
    region: int,
    p: field,
    c: float,
    rho: float,
    target: shape,
    inpolar: bool = False,
) -> list[iodata]: ...
@overload
def allextrapolateacousticfield(
    form: formulation,
    skinregion: int,
    region: int,
    p: field,
    c: float,
    rho: float,
    target: shape,
    targettimes: Sequence[float],
    samplestimes: Sequence[float],
    samplespdtpntp: Sequence[Sequence[field]],
) -> iodata: ...
def allextrapolateacousticfield(*args, **kwargs) -> Any: ...
def allfinalize() -> None:
    """
    <<INTERNAL>>
    Finalizes a DDM context.

    See Also
    --------
    allinitialize
    """
    ...

@overload
def allgather(fragment: Sequence[int], gathered: Sequence[int]) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def allgather(fragment: Sequence[float], gathered: Sequence[float]) -> None: ...
@overload
def allgather(
    fragment: Sequence[int], gathered: Sequence[int], fragsizes: Sequence[int]
) -> None: ...
@overload
def allgather(
    fragment: Sequence[float], gathered: Sequence[float], fragsizes: Sequence[int]
) -> None: ...
def allgather(*args, **kwargs) -> Any: ...
def allgetcoords(singlenodephysreg: int) -> list[float]:
    """
    This returns the x, y and z coordinates of a point physical region.
    If the physical region is empty an empty list is returned.
    If the physical region contains anything other than a single node, then an error is thrown.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> xyz_coords = qs.allgetcoords(singlenodephysreg)
    """
    ...

def allinitialize(verbosity: int = 1) -> None:
    """
    <<INTERNAL>>
    Initializes a DDM context. The `verbosity` sets the level of information detail for internal printing.

    See Also
    --------
    allfinalize
    """
    ...

def allintegrate(physreg: int, expr: expressionlike, integrationorder: int) -> float:
    """
    This integrates the **scalar** expression `expr` over the physical region `physreg`. The integration is exact up to the order of
    polynomials specified in the argument `integrationorder`.

    Note that integration is not allowed on a non-scalar expression.
    Typically `norm` or `comp` functions are used to obtain an equivalent scalar expression from a non-scalar expression to allow integration.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1"); x=field("x")
    >>> v.setorder(vol, 1)
    >>> v.setvalue(vol, 12*x)
    >>>
    >>> integratedvalue = allintegrate(vol, v, 4)

    For non-scalar expressions, use `norm` or `comp` to get its scalar equivalent before performing integration.
    >>> vectorexpr = array3x1(10,20,30)
    >>> normintgr = allintegrate(vol, norm(vectorexpr), 4)
    >>> compintgr = allintegrate(vol, comp(0,vectorexpr), 4)

    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> u.setvalue(vol, array3x1(12*x, x*x, 0))
    >>> normintgr = allintegrate(vol, norm(u), 4)
    >>> compintgr = allintegrate(vol, comp(0,u), 4)

    See Also
    --------
    allinterpolate, allprobe, allaverage
    """
    ...

def allinterpolate(
    physreg: int, expr: expressionlike, xyzcoords: Sequence[float]
) -> list[float]:
    """
    This interpolates the value of a **scalar** expression `expr` at points whose *x,y,z* coordinates are provided in the
    `xyzcoords` argument.

    Note that interpolation is not allowed on a non-scalar expression.
    Typically `norm` or `comp` functions are used to obtain an equivalent scalar expression from a non-scalar expression to allow interpolation.

    The flattened interpolated field values are returned if the point was found in the elements of the
    physical region `physreg`.
    If a requested interpolation point cannot be found (because it is outside of `physreg`
    or because the interpolation algorithm fails to converge, as can happen on curved 3D elements) then an
    error occurs.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1"); x=field("x")
    >>> v.setorder(vol, 1)
    >>> v.setvalue(vol, 12*x)
    >>> xyzcoord = [0.5,0.6,0.05]
    >>>
    >>> # Interpolation at a single point
    >>> singlepoint_interpolated = allinterpolate(vol, v, xyzcoord)
    >>>
    >>> # Interpolation at three points
    >>> multipoint_interpolated = allinterpolate(vol, v, [-1,0,0.1, 0,0,0.1, 1,0,0.1])
    >>>
    >>> # Interpolation of non-scalar expressions
    >>> w = field("h1xyz")
    >>> w.setorder(vol, 1)
    >>> w.setvalue(vol, array3x1(12*x, x*x, 0))
    >>> normintrp = allinterpolate(vol, norm(w), xyzcoord)
    >>> compintrp = allinterpolate(vol, comp(0,w), xyzcoord)

    See Also
    --------
    alllineinterpolate, allintegrate, allprobe, allaverage
    """
    ...

def allisempty(physreg: int) -> bool:
    """
    <<INTERNAL>>
    """
    ...

def alllaplace(
    physreg: int, regionv1: int, regionv0: int, coef: expressionlike, vorder: int
) -> field:
    return field()

def alllineinterpolate(
    physreg: int,
    expr: expressionlike,
    firstcoords: Sequence[float],
    lastcoords: Sequence[float],
    numsamples: int,
) -> list[float]:
    """
    This function interpolates the value of **scalar** expression `expr` at a series of points along a straight line
    inside a `physreg`. The line for interpolation is defined by a starting and an end point whose [x,y,z] coordinates
    are provided in the `firstcoords` and `lastcoords` arguments.
    The `numsamples` argument determines the number of sample points considered along the straight line.
    If a requested interpolation point along the line cannot be found (because it is outside of `physreg`
    or because the interpolation algorithm fails to converge, as can happen on curved 3D elements) then an
    error occurs.

    Note that interpolation is not allowed on a non-scalar expression.
    Typically `norm` or `comp` functions are used to obtain an equivalent scalar expression from a non-scalar expression to allow interpolation.

    This function in combination with `setoutputvalue` is used to make line plots in post-processing.

    Example
    -------
    >>> ...
    >>>
    >>> form.allsolve(relrestol=1e-06, maxnumit=1000, timestep=1e-6, maxnumnlit=-1)
    >>>
    >>> # parameters for line plot
    >>> xcoord = 0
    >>> ycoord = 0
    >>> zstart = -0.1
    >>> zend = 0.1
    >>> nsamples = 51
    >>> dz = (zend - zstart) / (nsamples - 1)
    >>>
    >>> # Magnetic flux density along Z-axis
    >>> B_axis = alllineinterpolate(reg.air, norm(B), [xcoord,ycoord,zstart], [xcoord,ycoord,zend], nsamples)
    >>> Z_coords = [zstart+i*dz for i in range(nsamples)]
    >>>
    >>> # Make the interpolated values available for plotting
    >>> setoutputvalue("B_axis",  B_axis, gettime())
    >>> setoutputvalue("Z-coord", Z_coords, gettime())

    See Also
    --------
    allinterpolate, allintegrate, allprobe, allaverage, alltimeinterpolate
    """
    ...

def allmax(physreg: int, expr: expressionlike, refinement: int) -> float:
    """
    This returns the maximum value of the expression `expr` obtained over the geometric region `physreg` by splitting all
    elements `refinement` times in each direction. Increasing the refinement will thus lead to a more accurate maximum value,
    but at an increased computational cost. The maximum value is exact when the refinement nodes added to the elements correspond
    to the position of maximum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the maximum
    is always exact to machine precision.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1"); x = field("x")
    >>> v.setorder(vol, 1)
    >>> v.setvalue(vol, 12*x)
    >>> maxdata = allmax(vol, v, 1)
    >>> maxdata
    12.0

    See Also
    --------
    allmin
    """
    ...

def allmeasuredistance(a: vec, b: vec, c: vec) -> float:
    """
    This returns a relative L2 norm according to the below formula:

    $$
    \\frac{|\\boldsymbol{a} - \\boldsymbol{b}|}{|\\boldsymbol{c}|}
    $$

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>>
    >>> projection = formulation()
    >>> projection += integral(vol, dof(v)*tf(v), 0, 2)
    >>> projection += integral(vol, dt(v)*tf(v) - 2*tf(v))
    >>> projection += integral(vol, dtdt(dof(v))*tf(v))
    >>>
    >>> v_prev = vec(projection) # previous iteration solution
    >>> v_curr = vec(projection) # current iteration solution
    >>>
    >>> relativeerror = 1.0
    >>> while(relativeerror < 1e-5):
    >>>     projection.allsolve(1e-6, 500)
    >>>     v_curr.setdata()
    >>>     relativeerror = allmeasuredistance(v_curr, v_prev, v_curr)
    >>>     v_prev = v_curr.copy()
    """
    ...

def allmin(physreg: int, expr: expressionlike, refinement: int) -> float:
    """
    This returns the minimum value of the expression `expr` obtained over the geometric region `physreg` by splitting all
    elements `refinement` times in each direction. Increasing the refinement will thus lead to a more accurate minimum value,
    but at an increased computational cost. The minimum value is exact when the refinement nodes added to the elements correspond
    to the position of minimum. For a first-order nodal shape function interpolation, on a mesh that is not curved, the minimum
    is always exact to machine precision.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1"); x = field("x")
    >>> v.setorder(vol, 1)
    >>> v.setvalue(vol, 12*x)
    >>> mindata = allmin(vol, v, 1)
    >>> mindata
    -2.0

    See Also
    --------
    allmax
    """
    ...

def allprobe(physreg: int, expr: expressionlike) -> float:
    """
    This functions returns the value of a scalar expression `expr` at the point region `physreg`.

    Example
    -------
    >>> vol=1; anynode=12
    >>> mymesh = mesh()
    >>> mymesh.selectanynode(anynode)
    >>> mymesh.load("disk.msh")
    >>>
    >>> x = field("x")
    >>> y = field("y")
    >>> probedvalue = allprobe(anynode, 2*x+y)
    """
    ...

def allsolve(
    relrestol: float,
    maxnumit: int,
    nltol: float,
    maxnumnlit: int,
    relaxvalue: float,
    formuls: Sequence[formulation],
    verbosity: int = 1,
) -> int:
    """
    This is a collective MPI operation and hence must be called by all ranks. It solves across all the ranks a nonlinear problem
    with a fixed-point iteration.

    Example
    -------
    >>> ...
    >>> allsolve(1e-8, 500, 1e-4, 1.0, [electrostatics])

    See Also
    --------
    solve, formulation.solve, formulation.allsolve
    """
    ...

def allstatictotransienthphi(
    H: field, phi: field, conductor: int, nonconductor: int, verbosity: int = 1
) -> tuple[field, field]:
    return (field(), field())

def alltimeinterpolate(
    physreg: int, expr: expressionlike, xyzcoord: Sequence[float], numtimesteps: int
) -> list[float]:
    """
    This function, for a given point with coordinates `xyzcoord` inside a `physreg`, interpolates the value of
    a **scalar** expression `expr` at a series of equidistant time instances over the time period corresponding
    to the fundamental frequency.
    The `numtimesteps` argument determines the number of time samples considered over the time period corresponding
    to the fundamental frequency.

    If a requested interpolation point cannot be found (because it is outside of `physreg`
    or because the interpolation algorithm fails to converge, as can happen on curved 3D elements) then an
    error occurs.

    Note that interpolation is not allowed on a non-scalar expression.
    Typically `norm` or `comp` functions are used to obtain an equivalent scalar expression from a non-scalar expression to allow interpolation.

    Example
    -------
    >>> # norm of Electric field signal interpolated over time
    >>> E_timeinterpolate = qs.alltimeinterpolate(reg.dielectric, norm(E), [xcoord,ycoord,zcoord], 101)

    See Also
    --------
    alllineinterpolate
    """
    ...

def andpositive(exprs: Sequence[expressionlike]) -> expression:
    """
    This returns an expression whose value is 1 for all evaluation points where the value of all the input expressions is larger
    or equal to zero. Otherwise, its value is -1.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> x=field("x"); y=field("y"); z=field("z")
    >>> expr = andpositive([x,y])      # At points, where x>=0 and y>=0, value is 1, otherwise -1.
    >>> expr.write(vol, "andpositive.vtk", 1)

    See Also
    --------
    ifpositive, orpositive
    """
    return expression()

def argZ(V: expressionlike, I: expressionlike) -> float:
    """
    This returns an expression that is the phase of the Z = V/I complex impedance.

    See Also
    --------
    realZ, imagZ, absZ
    """
    ...

def array1x1(arg0: expressionlike) -> expression:
    """
    This defines a vector or matrix operation of size $1\\times1$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 \\end{bmatrix}
    $$
    """
    return expression()

def array1x2(arg0: expressionlike, arg1: expressionlike) -> expression:
    """
    This defines a vector or matrix operation of size $1\\times2$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 & arg1 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array1x2(1,2)
    """
    return expression()

def array1x3(
    arg0: expressionlike, arg1: expressionlike, arg2: expressionlike
) -> expression:
    """
    This defines a vector or matrix operation of size $1\\times3$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 & arg1 & arg2 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array1x3(1,2,3)
    """
    return expression()

def array2x1(arg0: expressionlike, arg1: expressionlike) -> expression:
    """
    This defines a vector or matrix operation of size $2\\times1$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 \\cr arg1 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array2x1(1, 2)
    """
    return expression()

def array2x2(
    arg0: expressionlike,
    arg1: expressionlike,
    arg2: expressionlike,
    arg3: expressionlike,
) -> expression:
    """
    This defines a vector or matrix operation of size $2\\times2$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 & arg1 \\cr arg2 & arg3 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array2x2(1,2, 3,4)
    """
    return expression()

def array2x3(
    arg0: expressionlike,
    arg1: expressionlike,
    arg2: expressionlike,
    arg3: expressionlike,
    arg4: expressionlike,
    arg5: expressionlike,
) -> expression:
    """
    This defines a vector or matrix operation of size $2\\times3$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 & arg1 & arg2 \\cr arg3 & arg4 & arg5 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array2x3(1,2,3, 4,5,6)
    """
    return expression()

def array3x1(
    arg0: expressionlike, arg1: expressionlike, arg2: expressionlike
) -> expression:
    """
    This defines a vector or matrix operation of size $3\\times1$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 \\cr arg1 \\cr arg2 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array3x1(1, 2, 3)
    """
    return expression()

def array3x2(
    arg0: expressionlike,
    arg1: expressionlike,
    arg2: expressionlike,
    arg3: expressionlike,
    arg4: expressionlike,
    arg5: expressionlike,
) -> expression:
    """
    This defines a vector or matrix operation of size $3\\times2$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 & arg1 \\cr arg2 & arg3 \\cr arg4 & arg5 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array3x2(1,2, 3,4, 5,6)
    """
    return expression()

def array3x3(
    arg0: expressionlike,
    arg1: expressionlike,
    arg2: expressionlike,
    arg3: expressionlike,
    arg4: expressionlike,
    arg5: expressionlike,
    arg6: expressionlike,
    arg7: expressionlike,
    arg8: expressionlike,
) -> expression:
    """
    This defines a vector or matrix operation of size $3\\times3$. The array is populated in a row-major way.

    $$
    \\begin{bmatrix} arg0 & arg1 & arg2 \\cr arg3 & arg4 & arg5 \\cr arg6 & arg7 & arg8 \\end{bmatrix}
    $$

    Example
    -------
    >>> myarray = array3x3(1,2,3, 4,5,6, 7,8,9)
    """
    return expression()

def asin(input: expressionlike) -> expression:
    """
    This returns an expression that is the $arcsin$ or $sin^{-1}$ of input. The output expression is in `radians`.

    Example
    -------
    >>> expr = asin(sqrt(0.5))
    >>> expr.print();                    # in radians
    Expression size is 1x1
     @ row 0, col 0 :
    0.785398
    >>>
    >>> (expr * 180/getpi()).print();    # in degrees
    Expression size is 1x1
     @ row 0, col 0 :
    45

    See Also
    --------
    sin, cos, tan, acos, atan
    """
    return expression()

def atan(input: expressionlike) -> expression:
    """
    This returns an expression that is the $arctan$ or $tan^{-1}$ of input. The output expression is in `radians`.

    Example
    -------
    >>> expr = atan(0.57735)
    >>> expr.print();                    # in radians
    Expression size is 1x1
     @ row 0, col 0 :
    0.523599
    >>>
    >>> (expr * 180/getpi()).print();    # in degrees
    Expression size is 1x1
     @ row 0, col 0 :
    30

    See Also
    --------
    sin, cos, tan, asin, acos
    """
    return expression()

def atan2(y: expressionlike, x: expressionlike) -> expression:
    return expression()

def barrier() -> None:
    """
    <<INTERNAL>>
    This is a collective MPI operation (must be called by all ranks). Processing will be waiting until all ranks have reached this call.
    Note that if this function is not called by all the ranks, then the other ranks that call `barrier` will wait indefinitely.

    Example
    -------
    >>> import quanscient as qs
    >>> qs.barrier()
    """
    ...

def bode(reals: Sequence[float], imags: Sequence[float]) -> list[list[float]]:
    """
    This function returns the magnitudes (unit: dB) and angles (unit: degrees) of the given complex numbers.

    Example
    -------
    >>> magnitudes = qs.bode([1, 1, 0], [0, 1, 1])[0]
    >>> angles = qs.bode([1, 1, 0], [0, 1, 1])[1]
    >>> angles[1]
    45.0
    """
    ...

@overload
def broadcast(broadcaster: int, data: Sequence[int]) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def broadcast(broadcaster: int, data: Sequence[float]) -> None: ...
def broadcast(*args, **kwargs) -> Any: ...
def bulkviscosity(
    freq: expressionlike,
    rho: expressionlike,
    E: expressionlike,
    nu: expressionlike,
    dbpmpmhzP: expressionlike,
    dbpmpmhzS: expressionlike,
) -> expression:
    """
    This functions returns the bulk viscosity ($Pa \\cdot s$) of the elastic medium for the given attenuation coefficients and
    target frequency.
    The arguments `rho`, `E`, `nu` are respectively the density, Young's modulus, Poisson's ratio of the elastic medium which are
    used to calculate the speed of P-wave and S-wave.
    The arguments `dbpmpmhzP` and `dbpmpmhzS` are the **longitudinal** and **shear** attenuation coefficients
    respectively and must be provided in ($dB/m/MHz$).
    The conversion from ($dB/m/MHz$) to into ($Neper/m/MHz$) is taken care
    automatically in the function definition.

    The `freq` argument is the target frequency for the damping model with a linear relationship between frequency and damping.

    The bulk viscosity is given by
    $$
        \\nu_b = \\frac{2 \\alpha_p \\rho {v_p}^3 \\omega} {\\omega_{ref}^3} - \\frac{4}{3} \\nu_s \\qquad ; \\qquad
        \\nu_s = \\frac{2 \\alpha_s \\rho {v_s}^3 \\omega} {\\omega_{ref}^3} \\\\[10pt]
        v_p = \\sqrt{\\frac{E (1-\\nu)}{\\rho (1+\\nu)(1-2\\nu)}} \\qquad ; \\qquad
        v_s = \\sqrt{\\frac{E}{2 \\rho (1+\\nu)}} \\\\[10pt]
        \\omega_{target} = 2 \\pi f \\qquad ; \\qquad
        \\omega_{ref} = 2 \\pi \\times 10^6
    $$

    where,
    - $\\nu_b$ is the bulk viscosity ($Pa \\cdot s$),
    - $\\nu_s$ is the shear viscosity ($Pa \\cdot s$),
    - $\\alpha_p$ is the longitudinal attenuation coefficient ($Neper/m/MHz$),
    - $\\alpha_s$ is the shear attenuation coefficient ($Neper/m/MHz$),
    - $v_p$ is the speed of P-wave ($m/s$),
    - $v_s$ is the speed of S-wave ($m/s$),
    - $E$ is the Young's modulus ($Pa$),
    - $\\nu$ is the Poisson's ratio,
    - $\\rho$ is the density ($kg/m^3$),
    - $\\omega_{target}$ is target angular frequency ($rad/s$),
    - $\\omega_{ref}$ is the reference angular frequency ($rad/s$, corresponding to $1 \\, MHz$), and,
    - $f$ is target wave frequency ($Hz$).

    See Also
    --------
    bulkviscosityfromv, shearviscosity, shearviscosityfromv
    """
    return expression()

def bulkviscosityfromv(
    freq: expressionlike,
    rho: expressionlike,
    vp: expressionlike,
    vs: expressionlike,
    dbpmpmhzP: expressionlike,
    dbpmpmhzS: expressionlike,
) -> expression:
    """
    This functions returns the bulk viscosity ($Pa \\cdot s$) of the elastic medium for the given attenuation coefficients and
    target frequency.
    The argument `rho` is the density of the elastic medium.
    The arguments `vp` and `vs` correspond to the speed of P-wave and speed of S-wave in the medium.
    The arguments `dbpmpmhzP` and `dbpmpmhzS` are the **longitudinal** and **shear** attenuation coefficients
    respectively and must be provided in ($dB/m/MHz$).
    The conversion from ($dB/m/MHz$) to into ($Neper/m/MHz$) is taken care
    automatically in the function definition.

    The `freq` argument is the target frequency for the damping model with a linear relationship between frequency and damping.

    The bulk viscosity is given by
    $$
        \\nu_b = \\frac{2 \\alpha_p \\rho {v_p}^3 \\omega} {\\omega_{ref}^3} - \\frac{4}{3} \\nu_s \\qquad ; \\qquad
        \\nu_s = \\frac{2 \\alpha_s \\rho {v_s}^3 \\omega} {\\omega_{ref}^3} \\\\[10pt]
        \\omega_{target} = 2 \\pi f \\qquad ; \\qquad
        \\omega_{ref} = 2 \\pi \\times 10^6
    $$

    where,
    - $\\nu_b$ is the bulk viscosity ($Pa \\cdot s$),
    - $\\nu_s$ is the shear viscosity ($Pa \\cdot s$),
    - $\\alpha_p$ is the longitudinal attenuation coefficient ($Neper/m/MHz$),
    - $\\alpha_s$ is the shear attenuation coefficient ($Neper/m/MHz$),
    - $v_p$ is the speed of P-wave ($m/s$),
    - $v_s$ is the speed of S-wave ($m/s$),
    - $\\rho$ is the density ($kg/m^3$),
    - $\\omega_{target}$ is target angular frequency ($rad/s$),
    - $\\omega_{ref}$ is the reference angular frequency ($rad/s$, corresponding to $1 \\, MHz$), and,
    - $f$ is target wave frequency ($Hz$).

    See Also
    --------
    bulkviscosity, shearviscosity, shearviscosityfromv
    """
    return expression()

def cn(n: float) -> expression:
    """
    This function takes as an argument the fundamental frequency multiplier. It is a shortform for $cos(n * 2\\pi f t)$.

    Example
    -------
    >>> f = 15.5 * 1e+9  # fundamnetal frequency
    >>> setfundamentalfrequency(f)
    >>> drivingsignal = cn(2)  # same as cos(n* 2*getpi*f*t())

    See Also
    --------
    sn
    """
    return expression()

def comp(selectedcomp: int, input: expressionlike) -> expression:
    """
    This returns the selected component of a column vector expression. For a column vector expression, `selectedcomp` is 0 for
    the first, 1 for the second component and 2 for the third component respectively. For a matrix expression, the whole corresponding
    row is returned in the form of an expression. Thus, if `selectedcomp`, for example is 5, then an expression containing the entries of the
    fifth row of the matrix is returned.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> u.setvalue(vol, array3x1(10,20,30))
    >>> vecexpr = 2*(u+u)
    >>> comp(0, vecexpr).write(vol, "comp.vtk", 1)

    See Also
    --------
    compx, compy, compz
    """
    return expression()

def complexdivision(
    a: Sequence[expressionlike], b: Sequence[expressionlike]
) -> list[expression]:
    """
    Complexdivision computes the quotient `a / b` of two complex-valued scalar expressions `a` and `b`, which are presented as lists of length two (containing the real and imaginary parts).

    Example
    --------
    >>> quot = qs.complexdivision([-54, 23], [2, 7])
    >>> print(str(quot[0].evaluate()) + " + i * " + str(quot[1].evaluate()))
    1.0 + i * 8.0
    """
    ...

def complexinverse(a: Sequence[expressionlike]) -> list[expression]:
    """
    Complexinverse computes the inverse `1 / a` of a complex-valued scalar expression `a`, which is presented as a list of length two (containing the real and imaginary parts).

    Example
    --------
    >>> inv = qs.complexinverse([1, 2])
    >>> print(str(inv[0].evaluate()) + " + i * " + str(inv[1].evaluate()))
    0.2 + i * -0.4
    """
    ...

def complexproduct(
    a: Sequence[expressionlike], b: Sequence[expressionlike]
) -> list[expression]:
    """
    Complexproduct computes the product `a * b` of two complex-valued expressions `a` and `b`, which are presented as lists of length two (containing the real and imaginary parts).

    Example
    --------
    >>> prod = qs.complexproduct([1, 8], [2, 7])
    >>> print(str(prod[0].evaluate()) + " + i * " + str(prod[1].evaluate()))
    -54.0 + i * 23.0
    """
    ...

def compx(input: expressionlike) -> expression:
    """
    This returns the first or `x` component of a column vector expression. For a matrix expression, an expression containing the entries
    of the first row of the matrix is returned. This is equivalent to setting `selectedcomp=0` in `comp`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> u.setvalue(vol, array3x1(10,20,30))
    >>> vecexpr = 2*(u+u)
    >>> compx(vecexpr).write(vol, "compx.vtk", 1)

    See Also
    --------
    comp, compy, compz
    """
    return expression()

def compy(input: expressionlike) -> expression:
    """
    This returns the second or `y` component of a column vector expression. For a matrix expression, an expression containing the entries
    of the second row of the matrix is returned. This is equivalent to setting `selectedcomp=1` in `comp`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> u.setvalue(vol, array3x1(10,20,30))
    >>> vecexpr = 2*(u+u)
    >>> compx(vecexpr).write(vol, "compx.vtk", 1)

    See Also
    --------
    comp, compx, compz
    """
    return expression()

def compz(input: expressionlike) -> expression:
    """
    This returns the third or `z` component of a column vector expression. For a matrix expression, an expression containing the entries
    of the third row of the matrix is returned. This is equivalent to setting `selectedcomp=2` in `comp`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> u.setvalue(vol, array3x1(10,20,30))
    >>> vecexpr = 2*(u+u)
    >>> compx(vecexpr).write(vol, "compx.vtk", 1)

    See Also
    --------
    comp, compx, compy
    """
    return expression()

@overload
def contactcondition(
    gamma1: int,
    gamma1side: int,
    gamma2: int,
    gamma2side: int,
    u: field,
    spacing: expressionlike,
    stiction: expressionlike,
    lagmult: parameter,
) -> list[integration]:
    """
    <<INTERNAL>>
    """

@overload
def contactcondition(
    gamma1: int,
    gamma1side: int,
    gamma2: int,
    gamma2side: int,
    u: field,
    lagmult: parameter,
    spacing: expressionlike,
    stiction: expressionlike,
) -> tuple[
    list[integration], list[tuple[field, field, int, list[expression], expression, str]]
]: ...
def contactcondition(*args, **kwargs) -> Any: ...
@overload
def continuitycondition(
    gamma1: int,
    gamma2: int,
    u1: field,
    u2: field,
    errorifnotfound: bool = True,
    lagmultorder: int = 0,
) -> list[integration]:
    """
    This returns the formulation terms required to enforce field continuity.

    Examples
    --------
    **Example 1**: `continuitycondition(gamma1:int, gamma2:int. u1:field, u2:field, errorifnotfound:bool=True, lagmultorder:int=0)`
    >>> ...
    >>> u1 = field("h1xyz")
    >>> u2 = field("h1xyz")
    >>>
    >>> elasticity = formulation()
    >>> ...
    >>> elasticity += continuitycondition(gamma1, gamma2, u1, u2)

    This returns the formulation terms required to enforce $u_1 = u_2$ between boundary region $\\Gamma_1$ and $\\Gamma_2$ (with
    $\\Gamma_1 \\subseteq \\Gamma_2$, meshes can be non-matching). In case $\\Gamma_2$ is larger than $\\Gamma_1$ ($\\Gamma_1 \\subset
    \\Gamma_2$) the boolean flag `errorifnotfound` must be set to false.

    ***

    **Example 2:** `continuitycondition(gamma:int, gamma2:int, u1:field, u2:field, rotcent:List[double],
                                        rotangz:double, angzmod:double, factor:double, lagmultorder:int=0)`
    >>> ...
    >>> # Rotor-stator interface
    >>> rotorside=11; statorside=12
    >>> ...
    >>> # Rotor rotation around z axis
    >>> alpha = 30.0
    >>> ...
    >>> az = field("h1")
    >>> ...
    >>> magentostatics = formulation()
    >>> ...
    >>> magnetostatics += continuitycondition(statorside, rotorside, az, az, [0,0,0], alpha, 45.0, -1.0)

    This returns the formulation terms required to enforce field continuity across an $angzmod$ degrees slice of a rotor-stator
    interface where the rotor geometry is rotated by $rotangz$ around the $z$ axis with rotation center at $rotcent$. This
    situation arises for example in electric motor simulations when (anti)periodicity can be considered and thus only a slice
    of the entire 360 degrees needs to be simulated. Use a factor of -$1$ for antiperiodicity. Boundary $\\Gamma_1$ is the
    rotor-stator interface on the (non-moving) stator side while the boundary $\\Gamma_2$ is the interface on the rotor side. In
    the unrotated position the bottom boundary of the stator and rotor slice must be aligned with the $x$ axis.

    ***

    The condition is based on a Lagrange multiplier of the same type and the same harmonic content as the field $u_1$ and $u_2$. The
    mortar finite element method is used to link the unknown $dof$ field on $\\Gamma_1$ and $\\Gamma_2$ so that there is no
    restriction on the mesh used for both regions.

    See Also
    --------
    periodicitycondition, symmetrycondition
    """

@overload
def continuitycondition(
    gamma1: int,
    gamma2: int,
    u1: field,
    u2: field,
    rotcent: Sequence[float],
    rotangz: expressionlike,
    angzmod: float,
    factor: float,
    lagmultorder: int = 0,
) -> list[integration]: ...
def continuitycondition(*args, **kwargs) -> Any: ...
def cos(input: expressionlike) -> expression:
    """
    This returns an expression that is the $cos$ of input. The input expression is in `radians`.

    Example
    -------
    >>> expr = cos(getpi())
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    -1
    >>>
    >>> expr = cos(1)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    0.540302

    See Also
    --------
    sin, tan, asin, acos, atan
    """
    return expression()

def count() -> int:
    """
    This returns the number of processes/nodes/ranks used in the simulation.

    Example
    -------
    >>> import quanscient as qs
    >>> numranks = qs.count()

    See Also
    --------
    getrank
    """
    ...

def countphysicalram() -> int: ...
def crossproduct(a: expressionlike, b: expressionlike) -> expression:
    """
    This computes the cross-product of two vector expressions. The returned expression is a vector.
    $$
    \\boldsymbol{c} = \\boldsymbol{a} \\times \\boldsymbol{b}
    $$

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; top=3
    >>> E = field("hcurl")
    >>> n = normal(vol)
    >>> cp = crossproduct(E, n)
    """
    return expression()

def curl(input: expressionlike) -> expression:
    """
    This computes the curl of a vector expression. The returned expression is a vector.
    $$
    \\boldsymbol{w} = \\nabla \\times \\boldsymbol{u}
    $$

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1);
    >>> curl(u).write(vol, "curlu.vtk", 1)

    See Also
    --------
    grad, div
    """
    return expression()

def dbtoneper(toconvert: expressionlike) -> expression:
    """
    This converts the expression `toconvert` from a $dB$ units to $Nepers$.

    Example
    -------
    >>> neperattenuation = dbtoneper(100.0)
    """
    return expression()

def determinant(input: expressionlike) -> expression:
    """
    This returns the determinant of a square matrix.

    Example
    -------
    >>> matexpr = expression(3,3, [1,2,3, 6,5,4, 8,9,7])
    >>> detmat = determinant(matexpr)
    >>> detmat.print()
    Expression size is 1x1
     @ row 0, col 0 :
    21

    See Also
    --------
    inverse
    """
    return expression()

def detjac() -> expression:
    """
    This returns the determinant of the Jacobian matrix.

    Example
    -------
    >>> detJ = detjac()

    See Also
    --------
    jac, invjac
    """
    return expression()

def div(input: expressionlike) -> expression:
    """
    This computes the divergence of a vector expression. The returned expression is a scalar.
    $$
    s = \\nabla \\cdot \\boldsymbol{u}
    $$

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1);
    >>> div(u).write(vol, "divu.vtk", 1)

    See Also
    --------
    grad, curl
    """
    return expression()

@overload
def dof(input: expressionlike) -> expression:
    """
    This declares an unknown field (*dof* $\\$ for degree of freedom). The dofs are defined only on the region `physreg` which when
    not provided is set to the element integration region.

    Examples
    --------
    **Example 1**: `dof(input:expression)`
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>> projection = formulation()
    >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))

    **Example 2**: `dof(input:expression, physreg:int)`
    >>> ...
    >>> projection += integral(vol, dof(v, vol)*tf(v) - 2*tf(v))

    See Also
    --------
    tf
    """

@overload
def dof(input: expressionlike, physreg: int) -> expression: ...
def dof(*args, **kwargs) -> Any: ...
def doubledotproduct(a: expressionlike, b: expressionlike) -> expression:
    """
    This computes the double-dot product of two matrix expressions. The returned expression is a scalar.
    $$
    \\boldsymbol{A:B} = \\sum_{i,j} A_{ij} B_{ij}
    $$

    Example
    -------
    >>> a = array2x2(1,2, 3,4)
    >>> b = array2x2(11,12, 13, 14)
    >>> addotb = doubledotproduct(a, b)
    >>> addotb.print()
    Expression size is 1x1
     @ row 0, col 0 :
    130
    """
    return expression()

@overload
def dt(input: expressionlike) -> expression:
    """
    This returns the first-order time derivative expression.

    Examples
    --------
    **Example 1**: `dt(input:expression)`
    >>> ...
    >>> setfundamentalfrequency(50)
    >>> vmh = field("h1", [2,3])
    >>> vmh.setorder(vol, 1)
    >>> dt(vmh).write(vol, "dtv.vtk", 1)

    **Example 2**: `dt(input:expression, initdt:double, initdtdt)`

    This gives the transient approximation of the first-order time derivative of a space-independent expression. The
    initial values must be provided when using generalized alpha (`genalpha`) and are ignored otherwise.
    >>> ...
    >>> dtapprox = dt(t()*t(), 0, 2)

    See Also
    --------
    dtdt, dtdtdt, dtdtdtdt
    """

@overload
def dt(input: expressionlike, initdt: float, initdtdt: float) -> expression: ...
def dt(*args, **kwargs) -> Any: ...
@overload
def dtdt(input: expressionlike) -> expression:
    """
    This returns the second-order time derivative expression.

    Examples
    --------
    **Example 1**: `dtdt(input:expression)`
    >>> ...
    >>> setfundamentalfrequency(50)
    >>> vmh = field("h1", [2,3])
    >>> vmh.setorder(vol, 1)
    >>> dtdt(vmh).write(vol, "dtdtv.vtk", 1)

    **Example 2**: `dtdt(input:expression, initdt:double, initdtdt:double)`

    This gives the transient approximation of the second-order time derivative of a space-independent expression. The
    initial values must be provided when using generalized alpha (`genalpha`) and are ignored otherwise.
    >>> ...
    >>> dtapprox = dtdt(t()*t(), 0, 2)

    See Also
    --------
    dt, dtdtdt, dtdtdtdt
    """

@overload
def dtdt(input: expressionlike, initdt: float, initdtdt: float) -> expression: ...
def dtdt(*args, **kwargs) -> Any: ...
def dtdtdt(input: expressionlike) -> expression:
    """
    This returns the third-order time derivative expression.

    Example
    -------
    >>> ...
    >>> setfundamentalfrequency(50)
    >>> vmh = field("h1", [2,3])
    >>> vmh.setorder(vol, 1)
    >>> dtdtdt(vmh).write(vol, "dtdtdtv.vtk", 1)

    See Also
    --------
    dt, dtdt, dtdtdtdt
    """
    return expression()

def dtdtdtdt(input: expressionlike) -> expression:
    """
    This returns the fourth-order time derivative expression.

    Example
    -------
    >>> ...
    >>> setfundamentalfrequency(50)
    >>> vmh = field("h1", [2,3])
    >>> vmh.setorder(vol, 1)
    >>> dtdtdtdt(vmh).write(vol, "dtdtdtdtv.vtk", 1)

    See Also
    --------
    dt, dtdt, dtdtdt
    """
    return expression()

def dx(input: expressionlike) -> expression:
    """
    This returns the $x$ space derivative expression.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>> dx(v).write(vol, "dxv.vtk", 1)

    See Also
    --------
    dy, dz
    """
    return expression()

def dy(input: expressionlike) -> expression:
    """
    This returns the $y$ space derivative expression.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>> dy(v).write(vol, "dyv.vtk", 1)

    See Also
    --------
    dx, dz
    """
    return expression()

def dz(input: expressionlike) -> expression:
    """
    This returns the $z$ space derivative expression.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>> dz(v).write(vol, "dzv.vtk", 1)

    See Also
    --------
    dx, dy
    """
    return expression()

@overload
def elasticwavespeed(
    rho: expressionlike, E: expressionlike, nu: expressionlike
) -> list[expression]:
    """
    This function returns the speed of an $P$ and $S$-wave in a material whose density `rho` and elastic properties (`E, rho, or H`) are given.
    The unit of speed is in $m/s$.
    For isotropic materials, the elastic properties are provided through Young's modulus ($E$) and Poisson's ratio ($\\nu$).
    For a generic anisotropic materials, the elasticity tensor ($H$) must be passed as argument for the wave speed calculation.

    $$
    \\begin{align*}
        c_p &= \\sqrt{\\frac{E (1-\\nu)}{\\rho (1+\\nu)(1-2\\nu)}} \\\\[10pt]
        c_s &= \\sqrt{\\frac{E}{2\\rho (1+\\nu)}}
    \\end{align*}
    $$

    See Also
    --------
    emwavespeed, getc0
    """

@overload
def elasticwavespeed(rho: expressionlike, H: expressionlike) -> list[expression]: ...
def elasticwavespeed(*args, **kwargs) -> Any: ...
def elementwiseproduct(a: expressionlike, b: expressionlike) -> expression:
    """
    This computes the element-wise product of two matrix expressions `a` and `b`. The returned expression has the same size as the two input expressions.
    $$
    C_{ij} = A_{ij} B_{ij}
    $$

    Example
    -------
    >>> a = array2x2(1,2, 3,4)
    >>> b = array2x2(11,12, 13, 14)
    >>> aelwb = elementwiseproduct(a, b)
    >>> aelwb.print()
    Expression size is 2x2
     @ row 0, col 0 :
    11
     @ row 0, col 1 :
    24
     @ row 1, col 0 :
    39
     @ row 1, col 1 :
    56
    """
    return expression()

def emwavespeed(mu: expressionlike, eps: expressionlike) -> expression:
    """
    This returns the speed of an electromagnetic wave in a material whose magnetic permeability `mu` and
    electric permittivity `eps` are given. The unit of speed is in $m/s$.
    The permeability and permittivity are scalar value for isotropic materials, while they are tensors for a generic anisotropic materials.
    In case of anisotropic materials, the average of the trace of the tensor is used for the wave speed calculation.

    $$
        v = \\frac{1}{\\sqrt{\\mu \\; \\varepsilon}}
    $$

    See Also
    --------
    elasticwavespeed, getc0
    """
    return expression()

def entry(row: int, col: int, input: expressionlike) -> expression:
    """
    This gets the (`row`, `col`) entry in the `input` vector or matrix expression.

    Example
    -------
    >>> u = array3x2(1,2, 3,4, 5,6)
    >>> arrayentry_row2col0 = entry(2, 0, u)    # entry from third row (index=2), first column (index=0)
    >>> arrayentry_row2col0.print()
    Expression size is 1x1
     @ row 0, col 0 :
    5
    """
    return expression()

def errorif(
    expr: expressionlike, checkif: str, comparedto: float, name: str
) -> expression:
    return expression()

def evaluate(toevaluate: expressionlike) -> list[float]:
    """
    <<INTERNAL>>
    """
    ...

@overload
def exchange(
    targetranks: Sequence[int], sendvalues: Sequence[int], receivevalues: Sequence[int]
) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def exchange(
    targetranks: Sequence[int],
    sendvalues: Sequence[float],
    receivevalues: Sequence[float],
) -> None: ...
@overload
def exchange(
    targetranks: Sequence[int],
    sends: Sequence[Sequence[int]],
    receives: Sequence[Sequence[int]],
) -> None: ...
@overload
def exchange(
    targetranks: Sequence[int],
    sends: Sequence[Sequence[float]],
    receives: Sequence[Sequence[float]],
) -> None: ...
def exchange(*args, **kwargs) -> Any: ...
def exp(input: expressionlike) -> expression:
    """
    This returns an exponential function of base $e$:
    $$
    e^{input}
    $$

    Example
    -------
    >>> expr = exp(2)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    7.38906

    See Also
    --------
    pow
    """
    return expression()

def extrude(meshfile: str, height: float, numlayers: int) -> mesh:
    return mesh()

def eye(size: int) -> expression:
    """
    This returns a `size` x `size` identity matrix.

    Example
    -------
    >>> II = eye(2)
    >>> II.print()
    Expression size is 2x2
     @ row 0, col 0 :
    1
     @ row 0, col 1 :
    0
     @ row 1, col 0 :
    0
     @ row 1, col 1 :
    1
    """
    return expression()

def fieldorder(input: field, alpha: float = -1.0, absthres: float = 0.0) -> expression:
    """
    This returns an expression whose value is the interpolation order on each element for the provided `input` field. The value is a
    constant on each element. When the argument `alpha` is set, the value returned is the lowest order required to include
    `alpha` percentage of the total shape function coefficient weight. An additional optional argument `absthres` can be set to provide a
    minimum total weight below which the lowest possible field order is returned.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1; sur = 2; top = 3
    >>> v = field("h1")
    >>> v.setorder(vol, 2)
    >>> fo = fieldorder(v)
    >>> fo.write(vol, "fieldorder.vtk", 1)
    """
    return expression()

def finalize() -> None:
    """
    <<INTERNAL>>
    """
    ...

@overload
def gather(gatherer: int, fragment: Sequence[int], gathered: Sequence[int]) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def gather(
    gatherer: int, fragment: Sequence[float], gathered: Sequence[float]
) -> None: ...
@overload
def gather(
    gatherer: int,
    fragment: Sequence[int],
    gathered: Sequence[int],
    fragsizes: Sequence[int],
) -> None: ...
@overload
def gather(
    gatherer: int,
    fragment: Sequence[float],
    gathered: Sequence[float],
    fragsizes: Sequence[int],
) -> None: ...
def gather(*args, **kwargs) -> Any: ...
def getZ(V: expressionlike, I: expressionlike) -> complex:
    return complex(0, 0)

def getc0() -> float:
    """
    This returns the speed of light in vacuum in $m/s$.

    $$
        c_0 = \\frac{1}{\\sqrt{\\mu_0 \\; \\varepsilon_0}}
    $$

    See Also
    --------
    emwavespeed, elasticwavespeed
    """
    ...

def getcirculationports(
    harmonicnumbers: Sequence[int] = [],
) -> tuple[list[port], list[expression]]:
    return ([], [])

def getcirculationsources(
    circulations: Sequence[expressionlike],
    inittimederivatives: Sequence[Sequence[float]] = [],
) -> list[expression]: ...
def getdimension(physreg: int) -> int:
    """
    This returns the x, y and z mesh dimensions.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> dims = mymesh.getdimensions()
    """
    ...

def getepsilon0() -> float:
    """
    This returns the value of vacuum permittivity $\\epsilon_0 = 8.854187812813e-12 Fm^{-1}$.

    Example
    -------
    >>> eps0 = getepsilon0()
    8.854187812813e-12
    """
    ...

def getextrusiondata() -> list[expression]:
    """
    This gives the relative depth $\\delta$ in the extruded layer, the extrusion normal $\\boldsymbol{n}$ and tangents $\\boldsymbol{t_1}$
    and $\\boldsymbol{t_2}$. This is useful when creating Perfectly Matched Layers (PMLs).

    Example
    -------
    We use the `disk.msh` for the example here.
    >>> vol=1; sur=2; top=3; circle=4   # physical regions defined in disk.msh
    >>> mymesh = mesh()
    >>>
    >>> # predefine extrusion
    >>> volextruded=5; bndextruded=6;   # physical regions that will be utilized in extrusion
    >>> mymesh.extrude(volextruded, bndextruded, sur, [0.1,0.05])
    >>> mymesh.load("disk.msh")              # extrusion is performed when the mesh is loaded.
    >>> mymesh.write("diskpml.msh")
    >>> pmldata = getextrusiondata()

    See Also
    --------
    mesh.extrude
    """
    ...

def getharmonic(
    harmnum: int, input: expressionlike, numfftharms: int = -1
) -> expression:
    """
    This returns a single harmonic from a multi-harmonic expression. Set a positive last argument to use an FFT to compute the
    harmonic. The returned expression is on harmonic 1.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3
    >>> v = field("h1", [2])
    >>> v.setorder(vol, 1)
    >>> v.harmonic(2).setvalue(vol, 1)
    >>> constcomp = getharmonic(1, abs(v), 10)
    >>> constcomp.write(vol, "constcomp.pos", 1)
    """
    return expression()

def getmaxnumthreads() -> int:
    """
    <<INTERNAL>>
    This returns the maximum number of threads allowed.

    Example
    -------
    >>> setmaxnumthreads(2)
    >>> mnt = getmaxnumthreads()
    2

    See Also
    --------
    setmaxnumthreads
    """
    ...

def getmu0() -> float:
    """
    This returns the value of vacuum permeability $\\mu_0 = 1.2566370621219e-06 NA^{-2}$.

    Example
    -------
    >>> mu0 = getmu0()
    1.2566370621219e-06
    """
    ...

def getpi() -> float:
    """
    This returns value of $\\pi$.

    Example
    -------
    >>> pi = getpi()
    3.141592653589793
    """
    ...

def getrandom() -> float:
    """
    This returns a random value uniformly distributed between 0.0 and 1.0.

    Example
    -------
    >>> rnd = getrandom()
    """
    ...

def getrank() -> int:
    """
    This returns the rank of the current process/node.

    Example
    -------
    >>> import quanscient as qs
    >>> rank = qs.getrank()

    See Also
    --------
    count
    """
    ...

def getsstkomegamodelconstants() -> list[float]: ...
def getsubversion() -> int: ...
def gettime() -> float:
    """
    This gets the value of the time variable *t*.

    Example
    -------
    >>> settime(1e-3)
    >>> gettime()
    0.001

    See Also
    --------
    settime, t
    """
    ...

@overload
def gettotalforce(
    physreg: int,
    EorH: expressionlike,
    epsilonormu: expressionlike,
    extraintegrationorder: int = 0,
) -> list[float]:
    """
    This returns the components of the total magnetostatic/electrostatic force acting on a given region. In the axisymmetric
    case zero $x$ and $z$ components are returned and the $y$ component includes a $2 \\pi$ factor to provide the force acting
    on the corresponding 3D shape. Units are "$N$ per unit depth" in 2D and $N$ in 3D and 2D axisymmetry.

    Examples
    --------
    **Example 1**: `gettotalforce(physreg:int, EorH:expression, epsilonormu:expression, extraintegrationorder:int=0)`
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> phi = field("h1")
    >>> phi.setorder(vol, 2)
    >>>
    >>> mu0 = 4 * getpi() * 1e-7
    >>> mu = parameter()
    >>> mu.setvalue(vol, mu0)
    >>> totalforce = gettotalforce(vol, -grad(phi), mu)

    **Example 2**: `gettotalforce(physreg:int, meshdeform:expression, EorH:expression, epsilonormu:expression, extraintegrationorder:int=0)`

    This is similar to the above function but the total force is computed on the mesh deformed by the field `u`.
    >>> ...
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> totalforce = gettotalforce(vol, u, -grad(phi), mu)

    See Also
    --------
    printtotalforce
    """

@overload
def gettotalforce(
    physreg: int,
    meshdeform: expressionlike,
    EorH: expressionlike,
    epsilonormu: expressionlike,
    extraintegrationorder: int = 0,
) -> list[float]: ...
def gettotalforce(*args, **kwargs) -> Any: ...
def getturbulentpropertiessstkomegamodel(
    v: expressionlike,
    rho: expressionlike,
    viscosity: expressionlike,
    walldistance: expressionlike,
    kp: expressionlike,
    omegap: expressionlike,
    logomega: expressionlike,
) -> list[expression]: ...
def getversion() -> int: ...
def getversionname() -> str: ...
def getx() -> field:
    """
    This returns the $x$ coordinate.

    Example
    -------
    An expression for distance can be calculated as follows:
    >>> x = getx()
    >>> y = gety()
    >>> z = getz()
    >>> d = sqrt(x*x+y*y+z*z)

    See Also
    --------
    gety, getz
    """
    return field()

def gety() -> field:
    """
    This returns the $y$ coordinate.

    Example
    -------
    In CFD applications, a parabolic inlet velocity profile can be prescribed as follows:
    >>> y = gety()              # y coordinate
    >>> U = 0.3                 # maximum velocity
    >>> h = 0.41                # height of the domain
    >>> u = 4*U*y(h-y)/(h*h)    # parabolic inlet velocity profile expression

    See Also
    --------
    getx, getz
    """
    return field()

def getz() -> field:
    """
    This returns the $z$ coordinate.

    Example
    -------
    An expression for distance can be calculated as follows:
    >>> x = getx()
    >>> y = gety()
    >>> z = getz()
    >>> d = sqrt(x*x+y*y+z*z)

    See Also
    --------
    getx, gety
    """
    return field()

def grad(input: expressionlike) -> expression:
    """
    For a scalar input expression, this is mathematically treated as the gradient of a scalar ($\\nabla{v}$) and the output is a
    column vector with one entry per space derivative. For a vector input expression, this is mathematically treated as the gradient
    of a vector ($\\nabla{\\boldsymbol{u}}$) and the output has one row per component of the input and one column per space derivative.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1")
    >>> v.setorder(vol, 1);
    >>> grad(v).write(vol, "gradv.vtk", 1)

    See Also
    --------
    div, curl
    """
    return expression()

def greenlagrangestrain(input: expressionlike) -> expression:
    """
    This defines the (**nonlinear**) Green-Lagrange strains in Voigt form $(\\varepsilon_{xx},\\varepsilon_{yy},\\varepsilon_{zz},\\gamma_{yz},
    \\gamma_{xz},\\gamma_{xy})$. The input can either be the displacement field or its gradient.

    Note that the shear strain terms in the Voigt form are twice the values in tensorial form:
    $$
        \\gamma_{ij} = 2 \\varepsilon_{ij}
    $$

    The tensorial Green-Lagrange strain is defined as
    $$
        \\boldsymbol{\\varepsilon}_{\\tiny{GL}} = \\frac{1}{2}
                            \\left(
                                  \\nabla \\boldsymbol{u} + \\nabla \\boldsymbol{u}^T
                                + \\nabla \\boldsymbol{u}^T \\nabla \\boldsymbol{u}
                            \\right)
    $$

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> glstrain = greenlagrangestrain(u)
    >>> glstrain.print()

    See Also
    --------
    strain
    """
    return expression()

@overload
def grouptimesteps(
    filename: str, filestogroup: Sequence[str], timevals: Sequence[float]
) -> None:
    """
    This writes a .pvd ParaView file to group a set of .vtu files that are time solutions at the time values provided in
    `timevals`.

    Examples
    --------
    **Example 1**: `grouptimesteps(filename::str, filestogroup:List[str], timevals:List[double])`
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>> v.write(vol, "v1.vtu", 1)
    >>> v.write(vol, "v2.vtu", 1)
    >>> grouptimesteps("v.pvd", ["v1.vtu", "v2.vtu"], [0.0, 10.0])

    **Example 2**: `grouptimesteps(filename::str, fielprefix:str, firstint:int, timevals:List[double])`

    This is similar to the previous function except that the full list of file names to group does not have to be provided. The
    file names are constructed from the file prefix with an appended integer starting from 'firstint' by steps of 1. The filenames
    are ended with .vtu.
    >>> ...
    >>> grouptimesteps("v.pvd", "v", 1, [0.0, 10.0])
    """

@overload
def grouptimesteps(
    filename: str, fileprefix: str, firstint: int, timevals: Sequence[float]
) -> None: ...
def grouptimesteps(*args, **kwargs) -> Any: ...
def harm(harmnum: int, input: expressionlike, numfftharms: int = -1) -> expression:
    return expression()

@overload
def helmholtzkirchhoff(
    form: formulation,
    skinregion: int,
    region: int,
    p: field,
    c: float,
    rho: float,
    coords: Sequence[float],
) -> list[list[float]]: ...
@overload
def helmholtzkirchhoff(
    form: formulation,
    skinregion: int,
    region: int,
    p: field,
    c: float,
    rho: float,
    coords: Sequence[float],
    times: Sequence[float],
    samplestimes: Sequence[float],
    samplespdtpntp: Sequence[Sequence[field]],
) -> list[float]: ...
def helmholtzkirchhoff(*args, **kwargs) -> Any: ...
def ifpositive(
    condexpr: expressionlike, trueexpr: expressionlike, falseexpr: expressionlike
) -> expression:
    """
    This returns a conditional expression. The argument `condexpr` specifies the conditional argument. The expression value is
    `trueexpr` for all evaluation points where `condexpr` is larger or equal to zero. Otherwise, its value is `falseexpr`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1
    >>> x=field("x"); y=field("y"); z=field("z")
    >>> expr = ifpositive(x+y, 1, -1)   # At points, where x+y>=0, value is 1, otherwise -1.
    >>> expr.write(vol, "ifpositive.vtk", 1)

    See Also
    --------
    andpositive, orpositive
    """
    return expression()

def imagZ(V: expressionlike, I: expressionlike) -> float:
    """
    This returns an expression that is the imaginary part of the Z = V/I complex impedance.

    See Also
    --------
    realZ, absZ, argZ
    """
    ...

def initialize() -> None:
    """
    <<INTERNAL>>
    """
    ...

def initializelogs(format: logformat) -> None:
    """
    <<INTERNAL>> -- do not call in script

    Initializes the structured logging system

    Parameters
    ----------
    format : `logformat`
        Format for the logs. One of `logformat.plain` or `logformat.json`

    Raises
    ------
      None
    """
    ...

def insertrank(name: str) -> str: ...
@overload
def integral(
    physreg: int,
    tointegrate: expressionlike,
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> integration: ...
@overload
def integral(
    physreg: int,
    meshdeform: expressionlike,
    tointegrate: expressionlike,
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> integration: ...
@overload
def integral(
    physreg: int,
    numcoefharms: int,
    tointegrate: expressionlike,
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> integration: ...
@overload
def integral(
    physreg: int,
    numcoefharms: int,
    meshdeform: expressionlike,
    tointegrate: expressionlike,
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> integration: ...
@overload
def integral(
    physreg: int,
    tointegrate: tuple[expressionlike, preconditioner],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
@overload
def integral(
    physreg: int,
    meshdeform: expressionlike,
    tointegrate: tuple[expressionlike, preconditioner],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
@overload
def integral(
    physreg: int,
    numcoefharms: int,
    tointegrate: tuple[expressionlike, preconditioner],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
@overload
def integral(
    physreg: int,
    numcoefharms: int,
    meshdeform: expressionlike,
    tointegrate: tuple[expressionlike, preconditioner],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
@overload
def integral(
    physreg: int,
    tointegrate: Sequence[tuple[expressionlike, int, preconditioner]],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
@overload
def integral(
    physreg: int,
    meshdeform: expressionlike,
    tointegrate: Sequence[tuple[expressionlike, int, preconditioner]],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
@overload
def integral(
    physreg: int,
    numcoefharms: int,
    tointegrate: Sequence[tuple[expressionlike, int, preconditioner]],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
@overload
def integral(
    physreg: int,
    numcoefharms: int,
    meshdeform: expressionlike,
    tointegrate: Sequence[tuple[expressionlike, int, preconditioner]],
    integrationorderdelta: int = 0,
    blocknumber: int = 0,
) -> list[tuple[integration, preconditioner]]: ...
def integral(*args, **kwargs) -> Any: ...
def inverse(input: expressionlike) -> expression:
    """
    This returns the inverse of a square matrix.

    Example
    -------
    >>> matexpr = array2x2(1,2, 3,4)
    >>> invmat = inverse(matexpr)
    >>> invmat.print()
    Expression size is 2x2
     @ row 0, col 0 :
    -2
     @ row 0, col 1 :
    1
     @ row 1, col 0 :
    1.5
     @ row 1, col 1 :
    -0.5
    >>>
    >>> matexpr = expression(3,3, [1,2,3, 6,5,4, 8,9,7])
    >>> invmat = inverse(matexpr)

    See Also
    --------
    determinant
    """
    return expression()

@overload
def invjac(row: int, col: int) -> expression:
    """
    **Example 1: `invjac(row:int, col:int)`**

    This returns the inverse of the Jacobian matrix at the entry *(row, col)*.
    >>> Ji = invjac(1,2)

    **Example 2: `invjac()`**

    This returns the whole $3 \\times 3$ Jacobian matrix.
    >>> Ji = invjac()

    See Also
    --------
    jac, detjac
    """

@overload
def invjac() -> expression: ...
def invjac(*args, **kwargs) -> Any: ...
def isavailable() -> bool:
    """
    <<INTERNAL>>
    """
    ...

def iscontact(gamma1: int, lagmult: parameter) -> field:
    return field()

def isdefined(physreg: int) -> bool:
    """
    This checks if a physical region `physreg` is defined.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3; circle=4;
    >>> isdefined(sur)  # returns True as the physical region sur=2 is defined
    True
    >>>
    >>> isdefined(5)    # returns False as the mesh loaded has no physical region 5
    >>> False

    See Also
    --------
    isempty, isinside, istouching
    """
    ...

def isempty(physreg: int) -> bool:
    """
    This checks if a physical region `physreg` is empty.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3; circle=4;
    >>> isempty(sur)
    False

    See Also
    --------
    isdefined, isinside, istouching
    """
    ...

def isinside(physregtocheck: int, physreg: int) -> bool:
    """
    This checks if a physical region is fully included in another region.
    The `physreg` is the physical region with which `physregtocheck` is checked.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3; circle=4;
    >>> isinside(sur, vol)
    True
    >>>
    >>> isinside(vol, sur)
    False

    See Also
    --------
    isdefined, isempty, istouching
    """
    ...

def istouching(physregtocheck: int, physreg: int) -> bool:
    """
    This checks if a region is touching another region.
    The `physreg` is the physical region with which `physregtocheck` is checked.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3; circle=4;
    >>> istouching(sur, top)
    True

    See Also
    --------
    isdefined, isempty, isinside
    """
    ...

@overload
def itf(input: expressionlike) -> expression:
    """
    Otherwise the same as `tf` but the contributions in which this expression appears are multiplied by the imaginary unit when
    solving an eigenvalue problem based on a given formulation. This enables one to set up eigenvalue problems with complex matrices.

    Example
    --------
    >>> freq = 5e9
    >>> form = formulation()
    >>> form += integral(all, predefinedemwave(dof(E), tf(E), mu0, 0, epsilon0, 0, 0, 0))
    >>> form += integral(boundary, sqrt(sigma/(2.0 * mu0 * 2.0 * pi * freq)) * crossproduct(crossproduct(normal(), dt(dof(E))), normal()) * tf(E))
    >>> form += integral(boundary, sqrt(sigma/(2.0 * mu0 * 2.0 * pi * freq)) * crossproduct(crossproduct(normal(), dt(dof(E))), normal()) * itf(E))
    >>> eig = eigenvalue(form)
    >>> eig.settolerance(1e-12, 50)
    >>> eig.allcompute(1e-06, 1000, 1, 0.0, 2.0*pi*freq)

    See Also
    --------
    tf, eigenvalue
    """

@overload
def itf(input: expressionlike, physreg: int) -> expression: ...
def itf(*args, **kwargs) -> Any: ...
@overload
def jac(row: int, col: int) -> expression:
    """
    **Example 1: `jac(row:int, col:int)`**

    This returns the inverse of the Jacobian matrix at the entry *(row, col)*.
    >>> J = jac(1,2)

    **Example 2: `jac()`**

    This returns the whole $3 \\times 3$ Jacobian matrix.
    >>> J = jac()

    See Also
    --------
    invjac, detjac
    """

@overload
def jac() -> expression: ...
def jac(*args, **kwargs) -> Any: ...
def linspace(a: float, b: float, num: int) -> list[float]:
    """
    This gives a vector of `num` equally spaced values from `a` to `b`. The space between each values is calculated as:

    $$
    \\frac{b - a}{num -1}
    $$

    Example
    -------
    >>> vals = linspace(0.5, 2.5, 5)
    >>> printvector(vals)
    0.5 1 1.5 2 2.5

    See Also
    --------
    logspace
    """
    ...

def loadcirculationports(
    filename: str, ports: Sequence[port], exprs: Sequence[expressionlike]
) -> None: ...
def loadshape(meshfile: str) -> list[list[shape]]:
    """
    This function loads a mesh file to shapes. The output holds a shape for every physical region of dimension *d* (0D, 1D, 2D, 3D)
    defined in the mesh file. The loaded shapes can be edited (extruded, deformed, ...) and grouped with other shapes to create a
    new mesh. Note that the usage of loaded shapes might be more limited than other shapes.

    Example
    -------
    >>> diskshapes = loadshape("disk.msh")
    >>>
    >>> # Add a thin slice on top of the disk (diskshapes[2][1] is the top face of the disk)
    >>> thinslice = diskshapes[2][1].extrude(5, 0.02, 2)
    >>>
    >>> mymesh = mesh([diskshapes[2][0], diskshapes[2][1], diskshapes[3][0], thinslice])
    >>> mymesh.write("editeddisk.msh")
    """
    ...

def loadvector(
    filename: str, delimiter: str = ",", sizeincluded: bool = False
) -> list[float]:
    """
    This loads a list from the file `filename`. The `delimiter` specfies the character separating each entry in the file.
    The `sizeincluded` must be set to `True` if the first number in the file is the size of the list.

    Example
    -------
    >>> v = [2.4, 3.14, -0.1]
    >>> writevector("vecvals.txt", v, '\\n', True)
    >>> vloaded = loadvector("vecvals.txt", \\n', True)
    >>> vloaded
    [2.4, 3.14, -0.1]

    See Also
    --------
    printvector, writevector
    """
    ...

def log(input: expressionlike) -> expression:
    """
    This returns an expression that is the natural logarithm of the input expression.

    Example
    -------
    >>> expr = log(2);
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    0.693147

    See Also
    --------
    log10
    """
    return expression()

def log10(input: expressionlike) -> expression:
    """
    This returns an expression that is the base 10 logarithm of the input expression.

    Example
    -------
    >>> expr = log10(2);
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    0.30102999566

    See Also
    --------
    log
    """
    return expression()

def logspace(a: float, b: float, num: int, basis: float = 10.0) -> list[float]:
    """
    This returns the `basis` to the power of each of the `num` values in the linspace.

    Example
    -------
    >>> vals = logspace(1, 3, 3)    # resulting linspace: 1, 2, 3
    >>> printvector(vals)           # 10^1, 10^2, 10^3
    10 100 1000

    See Also
    --------
    linspace
    """
    ...

@overload
def makeharmonic(harms: Sequence[int], exprs: Sequence[expressionlike]) -> expression:
    """
    This returns a multi-harmonic expression whose harmonic numbers and expressions are provided as arguments. The argument
    expressions must be on harmonic 1.

    Example
    -------
    >>> ...
    >>> harmexpr = makeharmonic([1,2,4], [11, v.harmonic(2), 14])
    >>> harmexpr.write(vol, "harmexpr.pos", 1)
    """

@overload
def makeharmonic(
    harms: Sequence[int], expr: expressionlike, numfftharms: int
) -> expression: ...
def makeharmonic(*args, **kwargs) -> Any: ...
@overload
def max(a: expressionlike, b: expressionlike) -> expression:
    """
    This returns an expression whose value is the maximum of the two input arguments `a` and `b`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> x=field("x"); y=field("y"); z=field("z")
    >>> max(x,y).write(vol, "max.pos", 1)

    See Also
    --------
    min
    """

@overload
def max(a: field, b: field) -> expression: ...
@overload
def max(a: parameter, b: parameter) -> expression: ...
def max(*args, **kwargs) -> Any: ...
def meshsize(integrationorder: int) -> expression:
    """
    This returns an expression whose value is the length/area/volume for each 1D/2D/3D mesh element respectively. The value is
    constant on each mesh element. The `integrationorder` determines the accuracy of mesh size calculated. Higher the number,
    the better the accuracy. Integration order cannot be negative and if the integration order < $0$ a RuntimeError is raised.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1; sur = 2; top = 3
    >>> h = meshsize(0)
    >>> h.write(top, "meshsize.vtk", 1)
    """
    return expression()

@overload
def min(a: expressionlike, b: expressionlike) -> expression:
    """
    This returns an expression whose value is the minimum of the two input arguments `a` and `b`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> x=field("x"); y=field("y"); z=field("z")
    >>> min(x,y).write(vol, "min.pos", 1)

    See Also
    --------
    max
    """

@overload
def min(a: field, b: field) -> expression: ...
@overload
def min(a: parameter, b: parameter) -> expression: ...
def min(*args, **kwargs) -> Any: ...
def mod(input: expressionlike, modval: float) -> expression:
    """
    This is a modulo function. This returns an expression equal to the remainder resulting from the division
    of `input` by `modval`.

    Example
    -------
    >>> expr = mod(10, 9)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    1
    >>> expr = mod(99, 100)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    99
    >>> expr = mod(2.55, 0.6)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    0.15
    """
    return expression()

def modedrive(
    portphysreg: int,
    drivesignal: expressionlike,
    E: field,
    Etreal: expressionlike,
    Etimag: expressionlike,
    Htreal: expressionlike,
    Htimag: expressionlike,
    portnormal: Sequence[float],
    lumpfield: field,
    blocktag: int,
    extraintegrationorder: int = 0,
) -> list[integration]:
    """
    Modedrive defines a boundary condition in the physical region `portphysreg` by feeding and absorbing the mode found by alleigenport (parameters `Etreal`, `Etimag`, `Htreal`, and `Htimag`).
    The input field `E` is constrained to be a complex multiple of the mode; `lumpfield` defines this multiplier and must have been prepared into the formulation beforehand.
    If modedrive is applied with different modes in the same region, `E` is constrained to be their linear combination.
    The mode is fed according to `drivesignal`, which should be expressed as $\\sin(\\omega t + \\text{shift})$ or $\\cos(\\omega t + \\text{shift})$, where $\\omega$ is the driving frequency and $\\text{shift}$ is an optional phase shift.

    The parameter `blocktag` is the block number of the feeding term (for the absorbing term this is always 0).
    The feeding term only affects the right hand side, so this information can be used to solve the same formulation with multiple right hand sides, e.g. when computing S-parameters.

    Example
    -------
    >>> # Suppose a mesh has been loaded with physical regions (port1, port2, waveguide, pec_boundary) and E, mur, epsr_real, and eps_imag have been defined so that the following calls make sense:
    >>> port1mode0 = qs.alleigenport(port1, 1, 0, 1000, E, mur * qs.getmu0(), 0, epsr_real * qs.getepsilon0(), epsr_imag * qs.getepsilon0(), 0, 0, [0.0, 0.0, 1.0], 1e-06, 1000)[0]
    >>> port2mode0 = qs.alleigenport(port2, 1, 0, 1000, E, mur * qs.getmu0(), 0, epsr_real * qs.getepsilon0(), epsr_imag * qs.getepsilon0(), 0, 0, [0.0, 0.0, -1.0], 1e-06, 1000)[0]
    >>>
    >>> form = qs.formulation()
    >>>
    >>> # Prepare the lumpfield constraints:
    >>> lumpfields = form.lump([port1, port2], [2, 3])
    >>>
    >>> # Electromagnetic waves
    >>> form += qs.integral(waveguide, 3, qs.predefinedemwave(qs.dof(E), qs.tf(E), mur * qs.getmu0(), 0, epsr_real * qs.getepsilon0(), epsr_imag * qs.getepsilon0(), 0, 0, "oo2"))
    >>>
    >>> # Drive and absorb the mode of port1 (feeding term in block number 1):
    >>> form += qs.modedrive(port1, qs.sn(1), E, port1mode0[0], port1mode0[1], port1mode0[4], port1mode0[5], [0.0, 0.0, 1.0], lumpfields[0], 1)
    >>>
    >>> # Drive and absorb the mode of port2 (feeding term in block number 2):
    >>> form += qs.modedrive(port2, qs.sn(1), E, port2mode0[0], port2mode0[1], port2mode0[4], port2mode0[5], [0.0, 0.0, -1.0], lumpfields[1], 2)
    >>>
    >>> sols = form.allsolve(relrestol=1e-06, maxnumit=1000, nltol=1e-05, maxnumnlit=-1, relaxvalue=-1, rhsblocks=[[0, 1], [0, 2]])

    See Also
    --------
    alleigenport, formulation.allsolve, formulation.lump, allcomputesparameters
    """
    ...

def moveharmonic(
    origharms: Sequence[int],
    destharms: Sequence[int],
    input: expressionlike,
    numfftharms: int = -1,
) -> expression:
    """
    This returns an expression equal to the input expression with a selected and moved harmonic content. Set a positive last
    argument to use an FFT to compute the harmonics of the input expression.

    Example
    -------
    >>> ...
    >>> movedharm = moveharmonic([1,2], [5,3], 11+v)
    >>> movedharm.write("vol", "movedharm.pos", 1)
    """
    return expression()

@overload
def norm(expr: expressionlike) -> expression:
    """
    This gives the $L2$ norm of an expression input.

    Example
    -------
    >>> myvector = array3x1(1,2,3)
    >>> normL2 = norm(myvector)
    >>> normL2.print()
    Expression size is 1x1
     @ row 0, col 0 :
    3.74166
    """

@overload
def norm(
    harms: Sequence[int], expr: expressionlike, numfftharms: int = -1
) -> expression: ...
def norm(*args, **kwargs) -> Any: ...
@overload
def normal() -> expression:
    """
    This defines a normal vector with unit norm. If a physical region is provided as an argument then the normal points out of it.
    if no physical region is provided then the normal can be flipped depending on the element orientation in the mesh.

    Examples
    --------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3     # physical regions
    >>> normal(vol).write(sur, "normal.vtk", 1)
    """

@overload
def normal(pointoutofphysreg: int) -> expression: ...
def normal(*args, **kwargs) -> Any: ...
@overload
def on(
    physreg: int, expression: expressionlike, errorifnotfound: bool = True
) -> expression:
    """
    This function allows to use fields, unknown $dof$ fields or general expressions across physical regions with possibly non-
    matching meshes by evaluating the expression argument using a (x, y, z) coordinate interpolation. It makes it straightforward
    to setup the **mortar finite element method** to enforce general relations, such as field equality $u_1 = u_2$, at
    the interface $\\Gamma$ of non-matching meshes. This can for example be achieved with a Lagrange multiplier $\\lambda$ such that

    $$
    \\int_{\\Gamma} \\left( \\ \\lambda (u_1^{\\prime} - u_2^{\\prime}) + {\\lambda}^{\\prime} (u_1 - u_2) \\ \\right) d \\Gamma = 0
    $$

    holds for any appropriate field $u_1^{\\prime}$, $u_2^{\\prime}$ and ${\\lambda}^{\\prime}$. The example below illustrates the
    formulation terms needed to implement the Lagrange multiplier between interfaces $\\Gamma_1$ and $\\Gamma_2$.

    Examples
    --------
    **Example 1**: `on(physreg:int, expr:expression, errorifnotfound:bool=True)`

    `physreg` is the physical region across which the expression `expr` is evaluated. The `expr` argument can be fields or $dof$
    fields or any general expressions.

    >>> ...
    >>> u1=field("h1xyz"); u2=field("h1xyz"); lambda=field("h1xyz")
    >>> ...
    >>> elasticity = formulation()
    >>> ...
    >>> elasticity += integral(gamma1, dof(lambda)*tf(u1) )
    >>> elasticity += integral(gamma2, -on(gamma1, dof(lambda)) * tf(u2) )
    >>> elasticity += integral(gamma1, (dof(u1) - on(gamma2, dof(u2)))*tf(lambda) )

    When setting the flag `errorifnotfound=False`, any point in $\\Gamma_1$ without a relative in $\\Gamma_2$ (and vice versa)
    does not contribute to the assembled matrix. The default value is True for which an error is raised if a point in $\\Gamma_1$ is without
    a relative in $\\Gamma_2$ (and vice versa).

    The case where there is no unknown *dof* $\\$ term in the expression argument is described below:
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3
    >>> x=field("x"); y=field("y"); z=field("z"); v=field("h1")
    >>> v.setorder(vol, 1)
    >>> projection = formulation()
    >>> projection += integral(top, dof(v)*tf(v) - on(vol, dz(z))*tf(v))
    >>> projection.solve()
    >>> v.write(top, "dzz.pos", 1)

    With the *on* function, the (x, y, z) coordinates corresponding to each Gauss point of the integral are first calculated then the
    *dz(z)* $\\$ expression is evaluated through interpolation at these (x, y, z) coordinates on region *vol*. With *on* here *dz(z)*
    $\\$ is correctly evaluated as $1$ because the *z*-derivative calculation is performed on the volume region *vol*. Without the
    *on* operator the *z*-derivative would be wrongly calculated on the *top* face of the disk (a plane perpendicular to the *z*-axis).

    If a requested interpolation point cannot be found (because it is outside of *physreg* or because the interpolation algorithm
    fails to converge, as can happen on curved 3D elements) then an error occurs unless `errorifnotfound` is set to False. In the
    latter case, the value returned at any non-found coordinate is zero, without raising an error.


    **Example 2**: `on(physreg:int, expr:coordshift, expr:expression, errorifnotfound:bool=True)`

    This is similar to the previous example but here the (x, y, z) coordinates at which to interpolate the expression are shifted
    by (x+*compx(coordshift)*, y+*compy(coordshift)*, z+*compz(coordshift)*).
    >>> ...
    >>> projection += integral(top, dof(v)*tf(v) - on(vol, array3x1(2*x,2*y,2*z), dz(z))*tf(v))
    """

@overload
def on(
    physreg: int,
    coordshift: expressionlike,
    expression: expressionlike,
    errorifnotfound: bool = True,
) -> expression: ...
def on(*args, **kwargs) -> Any: ...
def orpositive(exprs: Sequence[expressionlike]) -> expression:
    """
    This returns an expression whose value is 1 for all evaluation points where at least one input expression has a value
    larger or equal to zero. Otherwise, its value is -1.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> x=field("x"); y=field("y"); z=field("z")
    >>> expr = orpositive([x,y])      # At points, where x>=0 or y>=0, value is 1, otherwise -1.
    >>> expr.write(vol, "orpositive.vtk", 1)

    See Also
    --------
    ifpositive, andpositive
    """
    return expression()

def periodicitycondition(
    gamma1: int,
    gamma2: int,
    u: field,
    dat1: Sequence[float],
    dat2: Sequence[float],
    factor: float,
    lagmultorder: int = 0,
) -> list[integration]:
    """
    This returns the formulation terms required to enforce on field $u$ a rotation or translation periodic condition between
    boundary region $\\Gamma_1$ and $\\Gamma_2$ (meshes can be non-conforming). A factor different than $1$ can be
    provided to scale the field on $\\Gamma_2$ (use -$1$ for antiperiodicity).

    Example
    -------
    >>> ...
    >>> u = field("h1xyz")
    >>> ...
    >>> elasticity = formulation()
    >>> ...
    >>> # In case gamma2 is gamma1 rotated by (ax, ay, az) degrees around first the x, then y and then z-axis.
    >>> # Rotation center is (cx, cy, cz)
    >>> cx=0; cy=0; cz=0
    >>> ax=0; ay=0; az=60
    >>>
    >>> elasticity += periodicitycondition(gamma1, gamma2, u, [cx,cy,cz], [ax,ay,az], 1.0)
    >>>
    >>> # In case gamma2 is gamma1 translated by a distance d in direction (nx, ny, nz)
    >>> d=0.8
    >>> nx=1; ny=0; nz=0
    >>> elasticity += periodicitycondition(gamma1, gamma2, u, [nx,ny,nz], [d], 1.0)

    The condition is based on a Lagrange multiplier of the same type and the same harmonic content as the field $u_1$ and $u_2$. The
    mortar finite element method is used to link the unknown $dof$ field on $\\Gamma_1$ and $\\Gamma_2$ so that there is no
    restriction on the mesh used for both regions.

    More advanced periodic conditions can be implemented easily using `on` function.

    See Also
    --------
    continuitycondition, symmetrycondition
    """
    ...

def pow(base: expressionlike, exponent: expressionlike) -> expression:
    """
    This is a power function. This returns an expression equal to `base` to the power `exponent`:
    $$
    {base}^{exponent}
    $$

    Example
    -------
    >>> expr = pow(2, 5)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    32

    See Also
    --------
    exp
    """
    return expression()

def powerlaw(
    j: expressionlike,
    jc: expressionlike,
    ec: expressionlike,
    n: expressionlike,
    sigmamin: float,
    sigmamax: float,
) -> expression:
    return expression()

def predefinedacousticradiation(
    dofp: expressionlike,
    tfp: expressionlike,
    soundspeed: expressionlike,
    density: expressionlike,
    neperattenuation: expressionlike,
) -> expression:
    """
    This function defines the equation for the Sommerfeld acoustic radiation condition

    $$
    \\partial_{\\boldsymbol{n}} p + \\frac{1}{c} \\frac{\\partial p}{\\partial t} = 0
    $$

    which forces the outgoing pressure waves at infinity: a pressure field of the form

    $$
    p(r, t) = P \\ cos(\\omega t - kr)
    $$

    propagating in the direction $\\boldsymbol{e_r}$ perpendicular to the truncation boundary indeed satisfies the Sommerfeld
    radiation condition since

    $$
        \\partial_{\\boldsymbol{n}} p = \\partial_{\\boldsymbol{e}_r} p = k \\ P \\ sin(\\omega t - kr)
        = \\frac{w}{c} \\ P \\ sin(\\omega t - kr) = - \\frac{1}{c} \\frac{\\partial (P \\ cos(\\omega t -kr))}{\\partial t}
    $$

    Zero artificial wave reflection at the truncation boundary happens only if it is perpendicular to the outgoing waves. In
    practical applications however the truncation boundary is not at an infinite distance from the acoustic source and the wave
    amplitude is not constant and thus, some level of artificial reflection cannot be avoided. To minimize this effect the
    truncation boundary should be placed as far as possible from the acoustic source (at least a few wavelengths away).

    An acoustic attenuation value can be provided (in $Neper/m$) in case of harmonic problems. For convenience use the function
    `dbtoneper` to convert $dB/m$ attenuation values to $Np/m$.

    Example
    -------
    >>> ...
    >>> acoustics += integral(sur, predefinedacousticradiation(dof(p), tf(p), 340, dbtoner(500)))
    """
    return expression()

def predefinedacousticstructureinteraction(
    dofp: expressionlike,
    tfp: expressionlike,
    dofu: expressionlike,
    tfu: expressionlike,
    soundspeed: expressionlike,
    normal: expressionlike,
    neperattenuation: expressionlike,
    scaling: float = 1.0,
) -> expression:
    """
    This function defines the bi-directional coupling for acoustic-structure interaction at the medium interface. Field $p$ is
    the acoustic pressure and field $\\boldsymbol{u}$ is the mechanical displacement. Calling $\\boldsymbol{n}$ the normal to
    the interface pointing out of the solid region, the bi-directional coupling is obtained by adding the fluid pressure loading
    to the structure

    $$
    \\boldsymbol{f}_{pressure} = -p \\boldsymbol{n}
    $$

    as well as linking the structure acceleration to the fluid pressure normal derivative using Newton's law:

    $$
    \\partial_{\\boldsymbol{n}} p = - \\rho_{fluid} \\frac{\\partial^2 \\boldsymbol{u}}{\\partial t^2} \\cdot \\boldsymbol{n}
    $$

    To have a good matrix conditioning a scaling factor $s$ (e.g $s = 1e10$) can be provided. In this case, the pressure source
    is divided by $s$ and, to compensate, the pressure force is multiplied by $s$. This leads to the correct membrane deflection
    but the pressure field is divided by the scaling factor.

    An acoustic attenuation value can be provided (in $Neper/m$) in case of harmonic problems. For convenience use the function
    `dbtoneper` to convert $dB/m$ attenuation values to $Np/m$.

    Example
    -------
    >>> ...
    >>> u = field("h1xy", [2,3])
    >>> u.setorder(sur, 2)
    >>> acoustics += integral(left, predefinedacousticstructureinteraction(dof(p), tf(p), dof(u), tf(u), 340, 1.2, array2x1(1,0), dbtoneper(500), 1e10)
    """
    return expression()

@overload
def predefinedacousticwave(
    dofp: expressionlike,
    tfp: expressionlike,
    soundspeed: expressionlike,
    density: expressionlike,
    neperattenuation: expressionlike,
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]:
    """
    This function defines the equation for (linear) acoustic wave propagation:

    $$
    \\nabla^2 p - \\frac{1}{c²} \\frac{\\partial^2 p}{\\partial t^2} = 0
    $$

    An acoustic attenuation value can be provided (in $Neper/m$) in case of harmonic problems. For convenience use the function
    `dbtoneper` to convert attenuation values from $dB/m$ to $Np/m$.

    The arguments have the following meaning:
    * `dofp`is the dof of the acoustic pressure field.
    * `tfp` is the test function of the acoustic pressure field.
    * `soundspeed` is the speed of sound in $m/s$.
    * `neperattenuation` is the attenuation in $Np/m$.
    * `pmlterms` is the list of pml terms.
    * `precondtype` is the type of precondition.

    Examples
    --------
    **Example 1**: `predefinedacousticwave(dofp:expression, tfp:expression, soundspeed:expression, neperattenuation:expression, precondtype:str="")`

    In the illustrative example below, a highly-attenuated acoustic wave propogation in a rectangular 2D box is simulated.
    >>> sur=1; left=2; wall=3
    >>> h=10e-3; l=50e-3
    >>> q = shape("quadrangle", sur, [0,0,0, l,0,0, l,h,0, 0,h,0], [250,50,250,50])
    >>> ll = q.getsons()[3]
    >>> ll.setphysicalregion(left)
    >>> lwall = shape("union", wall, [q.getsons()[0], q.getsons()[1], q.getsons()[2]])
    >>>
    >>> mymesh = mesh([q, ll, lwall])
    >>>
    >>> setfundamentalfrequency(40e3)
    >>>
    >>> # Wave propogation requires both the in-phase (2) and quadrature (3) harmonics:
    >>> p=field("h1", [2,3]); y=field("y")
    >>> p.setorder(sur, 2)
    >>> # In-phase only pressure source
    >>> p.harmonic(2).setconstraint(left, y*(h-y)/(h*h/4))
    >>> p.harmonic(3).setconstraint(left, 0)
    >>> p.setconstraint(wall)
    >>>
    >>> acoustics = formulation()
    >>> acoustics += integral(sur, predefinedacousticwave(dof(p), tf(p), 340, dbtoneper(500)))
    >>> acoustics.solve()
    >>> p.write(sur, "p.vtu", 2)
    >>>
    >>> # Write 50 timesteps for a time visualization
    >>> # p.write(sur, "p.vtu", 2, 50)

    **Example 2**: `predefinedacousticwave(dofp:expression, tfp:expression, soundspeed:expression, neperattenuation:expression, pmlterms:List[expression], precondtype:str="")`

    This is the same as the previous example but with PML boundary conditions.
    >>> ...
    >>> pmlterms = [detDr, detDi, Dr, Di, invDr, invDi]
    >>> acoustics += integral(sur, predefinedacousticwave(dof(p), tf(p), 340, 0, pmlterms))
    """

@overload
def predefinedacousticwave(
    dofp: expressionlike,
    tfp: expressionlike,
    soundspeed: expressionlike,
    density: expressionlike,
    neperattenuation: expressionlike,
    pmlterms: Sequence[expressionlike],
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
def predefinedacousticwave(*args, **kwargs) -> Any: ...
def predefinedadvectiondiffusion(
    doff: expressionlike,
    tff: expressionlike,
    v: expressionlike,
    alpha: expressionlike,
    beta: expressionlike,
    gamma: expressionlike,
    isdivvzero: bool = True,
) -> expression:
    """
    This defines the weak formulation for the generalized advection-diffusion equation:

    $$
    \\beta \\frac{\\partial c}{\\partial t}
    - \\nabla \\cdot \\left( \\boldsymbol{\\alpha} \\nabla c\\right)
    + \\gamma \\nabla \\cdot \\left( c \\boldsymbol{v} \\right)= 0
    $$

    where $c$ is the scalar quantity of interest and $\\boldsymbol{v}$ is the velocity that the quantity is moving with. With
    $\\beta$ and $\\gamma$ set to unit, the classical advection-diffusion equation with diffusivity
    tensor $\\boldsymbol{\\alpha}$ is obtained. Set `isdivvzero` to True if $\\nabla \\cdot \\boldsymbol{v}$ is zero (for
    incompressible flows).

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> T = field("h1")
    >>> v = field("h1xyz")
    >>> T.setorder(vol, 1)
    >>> v.setorder(vol, 1)
    >>> advdiff = formulation()
    >>> advdiff += integral(vol, predefinedadvectiondiffusion(dof(T), tf(T), v, 1e-4, 1.0, 1.0, True))

    See Also
    --------
    predefineddiffusion
    """
    return expression()

def predefinedaml(
    c: expressionlike, shifted: bool = False, reflectioncoef: float = 1e-05
) -> list[expression]: ...
def predefinedboxpml(
    pmlreg: int,
    innerreg: int,
    c: expressionlike,
    shifted: bool = False,
    reflectioncoef: float = 1e-05,
) -> list[expression]:
    """
    This is a collective MPI operation and hence must be called by all the ranks. This function returns

    $$
        \\Big[
            \\quad
            \\Re (|\\boldsymbol{D}|)    \\quad  \\Im (|\\boldsymbol{D}|)     \\quad
            \\Re (\\boldsymbol{D})      \\quad  \\Im (\\boldsymbol{D})       \\quad
            \\Re (\\boldsymbol{D}^{-1}) \\quad  \\Im (\\boldsymbol{D}^{-1})
            \\quad
        \\Big]
    $$

    where $\\boldsymbol{D}$ is the PML transformation matrix for a square box in a square box. A hyperbolic or shifted hyperbolic
    PML can be selected with `shifted` argument, and `reflectioncoef` gives the desired damping for transient problems.

    Example
    -------
    >>> ...
    >>> k = 2*getpi()*freq/c    # wave number
    >>> Dterms = predefinedboxpml(pmlreg, innerreg, k)
    """
    ...

def predefineddiffusion(
    doff: expressionlike,
    tff: expressionlike,
    alpha: expressionlike,
    beta: expressionlike,
) -> expression:
    """
    This defines the weak formulation for the generalized diffusion equation:

    $$
    \\beta \\frac{\\partial c}{\\partial t} - \\nabla \\cdot \\left( \\boldsymbol{\\alpha} \\nabla c\\right) = 0
    $$

    where $c$ is the scalar quantity of interest. With $\\beta$ set to unit, the classical diffusion equation with diffusivity
    tensor $\\boldsymbol{\\alpha}$ is obtained.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; top=3
    >>>
    >>> # Temperature field in [K]:
    >>> T = field("h1")
    >>> T.setorder(vol, 1)
    >>> T.setconstraint(top, 298)
    >>>
    >>> # Material properties:
    >>> k = 237.0   # thermal conductivity of aluminium [W/mK]
    >>> cp = 897.0  # heat capacity of aluminium [J/kgK]
    >>> rho = 2700  # density of aluminium [Kg/m^3]
    >>>
    >>> heatequation = formulation()
    >>> heatequation += integral(vol, predefineddiffusion(dof(T), tf(T), k, rho*cp))

    See Also
    --------
    predefinedadvectiondiffusion
    """
    return expression()

@overload
def predefinedelasticity(
    dofu: expressionlike, tfu: expressionlike, H: expressionlike
) -> expression:
    """
    This function returns the weak form of ($\\nabla \\cdot \\boldsymbol{\\sigma}$) term in the elasticity formulation for solid bodies.
    It can be used define the following formulations:
    - linear systems
    - nonlinear systems including geometric nonlinearity
    - proportional damping
    - prestressed structures

    Examples
    --------
    **Overload 1**: `predefinedelasticity(dofu:expression, tfu:expression, H:expression)`

    In this overload, the classical linear elasticity formulation is considered whose strong form is:
    $$
         - \\rho \\boldsymbol{\\ddot{u}} + \\nabla \\cdot \\boldsymbol{\\sigma} + \\boldsymbol{F} = 0
    $$
    where,
    - $\\boldsymbol{\\sigma}$ is the Cauchy stress tensor
    - $\\boldsymbol{u}$ is the displacement field vector
    - $\\boldsymbol{F}$ is the external body force vector

    The constitutive law relating stress to strain is given by the generalized Hooke's law. In Voigt notation this is
    $$
        \\boldsymbol{\\sigma} = \\boldsymbol{H} \\boldsymbol{\\varepsilon} \\\\[5pt]
    $$
    where,
    - $\\boldsymbol{H}$ is the $4^{th}$ order elasticity tensor
    - $\\boldsymbol{\\varepsilon}$ is the linear strain (in Voigt notation)

    The linear strain in tensorial form is given by
    $$
        \\boldsymbol{\\varepsilon} = \\frac{1}{2} \\Bigl[\\nabla \\boldsymbol{u} + \\bigl(\\nabla \\boldsymbol{u}\\bigr)^T  \\Bigr]
    $$

    This function can be used for isotropic or any general **anisotropic** materials. The elasticity tensor
    $\\boldsymbol{H}$ must be provided in *Pascal* units and should be such that it relates the stress and strain components
    in Voigt notation. If the Young's modulus $E$ and Poisson's ratio $\\nu$ of the material is known, then the function
    `EnutoH` can be used obtain the elasticity tensor.
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3
    >>>
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 2)
    >>> u.setconstraint(sur)
    >>>
    >>> # It is enough to only provide the lower triangular part of the elasticity matrix as it is symmetric
    >>> H = expression(6,6, [195e9, 36e9,195e9, 64e9,64e9,166e9, 0,0,0,80e9, 0,0,0,0,80e9, 0,0,0,0,0,51e9])
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), H))
    >>>
    >>> # Atmospheric pressure load (volumetric force) on top face deformed by field u (might require a nonlinear iteration)
    >>> elasticity += integral(top, u, -normal(vol)*1e5 * tf(u))
    >>>
    >>> elasticity.solve()
    >>> u.write(top, "u.vtk", 2)

    For **2D simulations**, the $6\\times6$ elasticity tensor must be transformed into $3\\times3$ using `Htoplanestrain`
    and `Htoplanestress` functions depending on which assumption is valid.
    >>> ...
    >>>
    >>> sur=1; bot=2; top=3
    >>>
    >>> u = field("h1xy") # two components in 2D
    >>> u.setorder(sur, 2)
    >>> u.setconstraint(bot)
    >>>
    >>> # It is enough to only provide the lower triangular part of the elasticity matrix as it is symmetric
    >>> H = expression(6,6, [195e9, 36e9,195e9, 64e9,64e9,166e9, 0,0,0,80e9, 0,0,0,0,80e9, 0,0,0,0,0,51e9])
    >>>
    >>> # Transform the 6x6 elasticity matrix to 3x3 for 2D
    >>> H2d = Htoplanestrain(H) # or Htoplanestress(H)
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(sur, predefinedelasticity(dof(u), tf(u), H2d))
    >>>
    >>> # Atmospheric pressure load (surface force) on top curve deformed by field u (uses a nonlinear iteration)
    >>> elasticity += integral(top, u, -normal(sur)*1e5 * tf(u))
    >>>
    >>> elasticity.solve()
    >>> u.write(sur, "u.vtk", 2)

    It is possible to include **Proportional damping** (also known as Rayleigh damping) in the linear elasticity formulation.
    The governing equation with Rayleigh damping terms is
    $$
        - \\rho \\boldsymbol{\\ddot{u}} + \\nabla \\cdot \\boldsymbol{\\sigma}
        + \\boldsymbol{F}
        + \\bigl[\\alpha(-\\rho \\dot{u})
        + \\beta(\\nabla \\cdot \\dot{\\boldsymbol{\\sigma}})\\bigr] = 0
    $$
    where $\\alpha$ is the mass proportional damping and $\\beta$ is the stiffness proportional damping.
    >>> ...
    >>>
    >>> elasticity = formulation()
    >>> # defines div(sigma) term
    >>> elasticity += integral(sur, predefinedelasticity(dof(u), tf(u), H))
    >>>
    >>> # Proportional damping
    >>> alpha = parameter(1, 1)
    >>> alpha.setvalue(all, 0.0)
    >>> alpha.setvalue(reg.proportional_damping_target, 1000.0)
    >>> beta = parameter(1, 1)
    >>> beta.setvalue(all, 0.0)
    >>> beta.setvalue(reg.proportional_damping_target, 0.0)
    >>> elasticity += integral(all, alpha * -rho * dt(dof(u)) * tf(u))
    >>> # defines beta*div(dt(sigma)) term
    >>> elasticity += integral(all, beta  *  predefinedelasticity(dt(dof(u)), tf(u), H))
    >>> ...
    >>>

    **Overload 2**: ```predefinedelasticity(dofu:expression, tfu:expression, u:field, H:expression, prestress:expression, dtstress:bool=False, linearized:bool=True)```

    In this overload, the elasticity formulation takes into account the **geometric nonlinearity** (total-Lagrangian formulation using
    Green-Lagrange strain tensor). The tensorial Green-Lagrange strain is defined as
    $$
        \\varepsilon_{\\tiny{GL}} = \\frac{1}{2}
                            \\left(
                                  \\nabla \\boldsymbol{u} + \\nabla \\boldsymbol{u}^T
                                + \\nabla \\boldsymbol{u}^T \\nabla \\boldsymbol{u}
                            \\right)
    $$

    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3
    >>>
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 2)
    >>>
    >>> ... # boundary conditions
    >>>
    >>> # It is enough to only provide the lower triangular part of the elasticity matrix as it is symmetric
    >>> H = expression(6,6, [195e9, 36e9,195e9, 64e9,64e9,166e9, 0,0,0,80e9, 0,0,0,0,80e9, 0,0,0,0,0,51e9])
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), u, H, 0))
    >>> elasticity += integral(vol, -2300*dtdt(dof(u)) * tf(u)); # 2300 is mass density
    >>>
    >>> ...

    Problems with large displacements and rotations such as buckling and snap-through can be simulated with this equation
    but **strains must always remain small**.
    Prestressed structures can also be simulated by providing the prestress vector in Voigt notation
    $(\\sigma_{xx},\\sigma_{yy},\\sigma_{zz},\\sigma_{yz},\\sigma_{xz},\\sigma_{xy})$.
    Set the prestress expression to $0$ for no prestress.

    >>> ...
    >>>
    >>> prestress = expression(6,1, [10e6,0,0,0,0,0])
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), u, H, prestress))
    >>> ...

    The proportional (Rayleigh) damping in elasticity formulation with geometric nonlinearity can be simulated by setting
    the the argument `dtstress=True`
    >>> ...
    >>>
    >>> elasticity = formulation()
    >>> # defines div(sigma) term, considers geoNL
    >>> elasticity += integral(sur, predefinedelasticity(dof(u), tf(u), u, H, 0))
    >>>
    >>> # Proportional damping
    >>> alpha = parameter(1, 1)
    >>> alpha.setvalue(all, 0.0)
    >>> alpha.setvalue(reg.proportional_damping_target, 1000.0)
    >>> beta = parameter(1, 1)
    >>> beta.setvalue(all, 0.0)
    >>> beta.setvalue(reg.proportional_damping_target, 0.0)
    >>> elasticity += integral(all, alpha * -rho * dt(dof(u)) * tf(u))
    >>> # defines beta*div(dt(sigma)) term, considers geoNL
    >>> elasticity += integral(all, beta  *  predefinedelasticity(dt(dof(u)), tf(u), u, H, 0, True))
    >>> ...
    >>>

    The weak form of ($\\nabla \\cdot \\boldsymbol{\\sigma}$) term is nonlinear when geometric nonlinearity is considered.
    The boolean argument `linearized` decides whether this term is linearized or not. By default this is set to True.
    If set to False, then fixed point iteration is utilized.

    See Also
    --------
    EnutoH, Htoplanestrain, Htoplanestress
    """

@overload
def predefinedelasticity(
    dofu: expressionlike,
    tfu: expressionlike,
    u: field,
    H: expressionlike,
    prestress: expressionlike,
    dtstress: bool = False,
    linearized: bool = True,
) -> expression: ...
def predefinedelasticity(*args, **kwargs) -> Any: ...
def predefinedelasticradiation(
    dofu: expressionlike, tfu: expressionlike, rho: expressionlike, H: expressionlike
) -> expression:
    return expression()

@overload
def predefinedelasticwave(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    Eyoung: expressionlike,
    nupoisson: expressionlike,
    bulkviscosity: expressionlike,
    shearviscosity: expressionlike,
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
@overload
def predefinedelasticwave(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    Eyoung: expressionlike,
    nupoisson: expressionlike,
    bulkviscosity: expressionlike,
    shearviscosity: expressionlike,
    pmlterms: Sequence[expressionlike],
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
@overload
def predefinedelasticwave(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    Hr: expressionlike,
    Hi: expressionlike,
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
@overload
def predefinedelasticwave(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    Hr: expressionlike,
    Hi: expressionlike,
    pmlterms: Sequence[expressionlike],
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
@overload
def predefinedelasticwave(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    H: expressionlike,
    alpha: expressionlike,
    beta: expressionlike,
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
@overload
def predefinedelasticwave(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    H: expressionlike,
    alpha: expressionlike,
    beta: expressionlike,
    pmlterms: Sequence[expressionlike],
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
def predefinedelasticwave(*args, **kwargs) -> Any: ...
@overload
def predefinedelasticwavefromv(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    vp: expressionlike,
    vs: expressionlike,
    bulkviscosity: expressionlike,
    shearviscosity: expressionlike,
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
@overload
def predefinedelasticwavefromv(
    dofu: expressionlike,
    tfu: expressionlike,
    rho: expressionlike,
    vp: expressionlike,
    vs: expressionlike,
    bulkviscosity: expressionlike,
    shearviscosity: expressionlike,
    pmlterms: Sequence[expressionlike],
    precondtype: str = "",
) -> list[tuple[expression, int, preconditioner]]: ...
def predefinedelasticwavefromv(*args, **kwargs) -> Any: ...
def predefinedelectrostaticforce(
    input: expressionlike, E: expressionlike, epsilon: expressionlike
) -> expression:
    """
    This function defines the weak formulation term for electrostatic forces. The first argument is the mechanical displacement test
    function or its gradient, the second is the electric field expression and the third argument is the electric permittivity (
    must be a scalar).

    Let us call $\\boldsymbol{T}$  [$N/m^2$] the electrostatic Maxwell stress tensor:
    $$
    \\boldsymbol{T} = \\epsilon \\ \\boldsymbol{E} \\otimes \\boldsymbol{E}
                        -
                    \\frac{1}{2} \\epsilon \\left( \\boldsymbol{E} \\cdot \\boldsymbol{E} \\right) \\ \\boldsymbol{I}
    $$
    where $\\epsilon$ is the electric permittivity, $\\boldsymbol{E}$ is the electric field and $\\boldsymbol{I}$ is the identity matrix.
    The electrostatic force density is $\\nabla \\cdot \\boldsymbol{T} [$N/m^3$]$ so that the loading for a mechanical problem can
    be obtained by adding the following term:
    $$
    \\int_{\\Omega} \\left( \\nabla \\cdot \\boldsymbol{T} \\right) \\cdot \\boldsymbol{u}^{\\prime} d\\Omega
    $$
    where $\\boldsymbol{u}$ is the mechanical displacement. The term can be rewritten in the form that is provided by this function:
    $$
    -\\int_{\\Omega} \\boldsymbol{T} \\ \\boldsymbol{\\epsilon}^{\\prime} d\\Omega
    $$
    where $\\boldsymbol{\\epsilon}$ is the infinitesimal strain tensor. This is identical to what is obtained using the virtual
    work principle. For details refer to *'Domain decomposition techniques for the nonlinear, steady state, finite element
    simulation of MEMS ultrasonic transducer arrays'*, page 40.

    In this function, a region should be provided to the test function argument to compute the force only for the degrees of
    freedom associated to that specific region (in the example below with *tf(u, top)* the force only acts on the surface region 'top'.
    In any case, a **correct force calculation requires including** in the integration domain all elements in the region where
    the force acts and in the **element layer around it** (in the example below 'vol' includes all volume elements touching
    surface 'top').

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; top=3
    >>> v=field("h1"); u=field("h1xyz")
    >>> v.setorder(vol,1)
    >>> u.setorder(vol,2)
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e9, 0.3))
    >>> elasticity += integral(vol, predefinedelectrostaticforce(tf(u,top), -grad(v), 8.854e-12))

    See Also
    --------
    predefinedmagnetostaticforce
    """
    return expression()

def predefinedelectrostatics(
    dofv: expressionlike,
    tfv: expressionlike,
    epsilon: expressionlike,
    precondtype: str = "",
) -> tuple[expression, preconditioner]:
    """
    <<INTERNAL>>
    """
    return (expression(), preconditioner())

def predefinedemboundaryadmittance(
    dofE: expressionlike, tfE: expressionlike, Yr: expressionlike, Yi: expressionlike
) -> expression:
    return expression()

@overload
def predefinedemwave(
    dofE: expressionlike,
    tfE: expressionlike,
    mur: expressionlike,
    mui: expressionlike,
    epsr: expressionlike,
    epsi: expressionlike,
    sigr: expressionlike,
    sigi: expressionlike,
    precondtype: str = "",
    eigenmodecalc: bool = False,
) -> tuple[expression, preconditioner]:
    """
    This defines the equation for (linear) electromagnetic wave propagation:

    $$
        \\nabla \\times \\left( \\frac{1}{\\mu} \\nabla \\times \\boldsymbol{E} \\right) +
        \\sigma \\frac{\\partial \\boldsymbol{E}}{\\partial t} +
        \\epsilon \\frac{\\partial^2 \\boldsymbol{E}}{\\partial t^2} = 0
    $$

    where $\\boldsymbol{E}$ is the electric field, $\\mu$ is the magnetic permeability, $\\epsilon$ is the electric permiitivity
    and $\\sigma$ is the electric conductivity. The real and imaginary parts of each material property can be provided.

    The argument have the following meaning:
    * `dofE` is the dof of the electric field.
    * `tfE` is the test function of the electric field.
    * `mur` and `mui` is the real and imaginary part of the magnetic permeability $\\mu$.
    * `epsr` and `epsi` is the real and imaginary part of the electric permittivity $\\epsilon$.
    * `sigr` and `sigi` is the real and imaginary part of the electric conductivity $\\sigma$.
    * `pmlterms` is the list of pml terms.
    * `precondtype` is the type of precondition.

    Examples
    --------
    **Example 1**: `predefinedemwave(dofE:expression, tfE:expression, mur:expression, mui:expression, epsr:expression, epsi:expression, sigr:expression, sigi:expression, precondtype:str="")`
    >>> ...
    >>> E = field("hcurl", [2,3])
    >>> ...
    >>> maxwell += integral(sur, predefinedemwave(dof(E), tf(E), mu0,0, epsilon0,0, 0,0))

    **Example 2**: `predefinedemwave(dofE:expression, tfE:expression, mur:expression, mui:expression, epsr:expression, epsi:expression, sigr:expression, sigi:expression, pmlterms:List[expression], precondtype:str="")`

    This is the same as the previous example but with PML boundary conditions.
    >>> ...
    >>> pmlterms = [detDr, detDi, Dr, Di, invDr, invDi]
    >>> maxwell += integral(sur, predefinedemwave(dof(E), tf(E), mu0,0, epsilon0,0, 0,0, pmlterms))
    """

@overload
def predefinedemwave(
    dofE: expressionlike,
    tfE: expressionlike,
    mur: expressionlike,
    mui: expressionlike,
    epsr: expressionlike,
    epsi: expressionlike,
    sigr: expressionlike,
    sigi: expressionlike,
    pmlterms: Sequence[expressionlike],
    precondtype: str = "",
    eigenmodecalc: bool = False,
) -> tuple[expression, preconditioner]: ...
def predefinedemwave(*args, **kwargs) -> Any: ...
@overload
def predefinedfluidstructureinteraction(
    fsireg: int,
    fluidreg: int,
    dofv: expressionlike,
    tfv: expressionlike,
    v: field,
    dofp: expressionlike,
    dofu: expressionlike,
    tfu: expressionlike,
) -> expression:
    """
    This function returns the formulation of fluid-structure interaction for incompressible flows:

    The Navier-Stokes equation for incompressible flows in weak form is given by
    $$
        \\int_{\\Omega} \\frac{\\partial \\rho}{\\partial t} \\cdot p^{\\prime} d\\Omega + \\int_{\\Omega}  (\\rho \\nabla \\cdot \\mathbf{v}) {p^{\\prime}} d\\Omega = 0 
    $$

    $$
    \\begin{align*}
        \\int_{\\Omega} \\rho \\frac{\\partial \\mathbf{v}}{\\partial t} \\cdot \\mathbf{v^{\\prime}}  d\\Omega 
        + \\int_{\\Omega} \\rho (\\mathbf{v} \\cdot \\nabla \\mathbf{v}) \\cdot \\mathbf{v^{\\prime}}  d\\Omega = 
        & - \\int_{\\Omega} \\nabla p \\cdot \\mathbf{v^{\\prime}}  d\\Omega \\\\
        & - \\int_{\\Omega} \\mu (\\nabla \\mathbf{v} + \\nabla \\mathbf{v}^T)\\cdot \\nabla \\mathbf{v^{\\prime}}  d\\Omega \\\\
        & + \\int_{\\Gamma} \\mu (\\nabla \\mathbf{v} + \\nabla \\mathbf{v}^T)\\cdot \\mathbf{n} \\cdot \\mathbf{v^{\\prime}}  d\\Gamma \\\\
    \\end{align*} 
    $$

    where $\\mathbf{v}$ is the velocity, $p$ the pressure, $\\mathbf{u}$ the displacement of the structure, $\\Omega$ the fluid domain, and $\\Gamma$ the whole boundary of the fluid domain. The dashed variables are the test functions in the weak formulation.

    The no-slip boundary condition at the fluid-structure interface is applied by using a Lagrange multiplier ($\\boldsymbol{\\lambda}$) method as
    $$
        \\int_{\\Gamma_{\\text{fsi}}} \\Bigl( \\left(\\mathbf{v} - \\dot{\\mathbf{u}} \\right) \\cdot \\boldsymbol{\\lambda^{\\prime}} +  \\boldsymbol{\\lambda} \\cdot \\mathbf{v}^{\\prime} \\Bigr) d\\Gamma_{\\text{fsi}} = 0
    $$

    The Lagrange multiplier $\\boldsymbol{\\lambda}$ naturally contains the viscous forces acting on the fluid, which can be applied directly to the structure with an inverted sign along with the normal pressure force as
    $$
        \\int_{\\Gamma_{\\text{fsi}}} (p \\mathbf{n} -\\boldsymbol{\\lambda})\\cdot \\mathbf{u}^{\\prime}  d\\Gamma_{\\text{fsi}} = 0
    $$

    where $\\Gamma_{\\text{fsi}}$ the boundary interface between fluid and structure domains.

    Example
    -------
    >>> mymesh = mesh("micropillar.msh")
    >>> solid = 1           # physical region
    >>> fluid = 2           # physical region
    >>> fsinterface = 3     # Fluid-structure interface region
    >>>
    >>> v=field("h1xyz"); p=field("h1"); u=field("h1xyz")
    >>> v.setorder(fluid, 2)
    >>> p.setorder(fluid, 1)    # Satisfies the LBB condition
    >>>
    >>> fsi = formulation()
    >>> fsi += integral(solid, predefinedelasticity(dof(u), tf(u), H))
    >>> fsi += integral(fluid, umesh, predefinednavierstokes(dof(v), tf(v), v, dof(p), tf(p), 8.9e-4, 1000, 0, 0))
    >>> fsi += integral(fsinterface, umesh, predefinedfluidstructureinteraction(fsinterface, fluid, dof(v), tf(v), v, dof(p), dof(u), tf(u)))

    See Also
    --------
    predefinednavierstokes
    """

@overload
def predefinedfluidstructureinteraction(
    fsireg: int,
    dofv: expressionlike,
    tfv: expressionlike,
    v: field,
    dofu: expressionlike,
    tfu: expressionlike,
) -> expression: ...
def predefinedfluidstructureinteraction(*args, **kwargs) -> Any: ...
@overload
def predefinedlinearpoissonwalldistance(
    physreg: int,
    wallreg: int,
    interpolationorder: int = 1,
    relresddmtol: float = 1e-12,
    maxnumddmit: int = 500,
    relerrnltol: float = 1e-06,
    maxnumnlit: int = 100,
    project: bool = True,
    verbosity: int = 1,
) -> expression:
    """
    This function calculates and returns distance values from the wall based on the linear Poisson wall distance equation:

    $$
    \\begin{align*}
      \\nabla \\cdot (\\nabla \\phi) + 1 & = 0  \\qquad &on \\ \\ &\\Omega        \\\\[5pt]
      \\phi & = 0                               \\qquad &on \\ \\ &\\Gamma_u      \\\\[5pt]
      \\frac{d \\phi}{dn} & = 0                 \\qquad &on \\ \\ &\\Gamma_{N}
    \\end{align*}
    $$

    where $\\phi$ is the approximate wall distance function. The distance is calculated for the physical region *physreg* from
    the walls defined in *wallreg* argument.

    More information can be found in *Computations of Wall Distances Based on Differential Equations
    Paul G. Tucker, Chris L. Rumsey, Philippe R. Spalart, Robert E. Bartels, and Robert T. Biedron
    AIAA Journal 2005 43:3, 539-549, https://doi.org/10.2514/1.8626 .*

    The system is linear and hence a linear solver is used. After calculating the distance function $\\phi$, a better approximation
    of distance is obtained as follows:

    $$
    d(\\phi) = - | \\nabla \\phi | \\pm \\sqrt{| \\nabla \\phi|^2 + 2 \\phi}
    $$

    This wall distance uses an above-zero limiter during calculation. Thus, to ensure
    that the distance value obtained is smooth, set the *project* argument to True. This will solve a projection of the distance
    values at the end and return a smooth solution.

    **Excerpts from the above paper**:
    "The derivation of the above formula for $d(\\phi)$ assumes extensive (infinite) coordinates in the non-normal wall directions.
    Hence, the distance is only accurate close to walls. However, turbulence models only need 'd' accurate close to walls."

    Example
    -------
    >>> mymesh = mesh("2D_Flatplate_35x25.msh")
    >>>
    >>> # physical regions
    >>> fluid=1, inlet=2, outlet=3, top=4, bot_upstream=5, plate=6
    >>>
    >>> linearpoisson_wd = predefinedlinearpoissonwalldistance(fluid, wall);

    See Also
    --------
    predefinedreciprocalwalldistance, predefinednonlinearpoissonwalldistance
    """

@overload
def predefinedlinearpoissonwalldistance(
    physreg: int,
    meshdeform: expressionlike,
    wallreg: int,
    interpolationorder: int = 1,
    relresddmtol: float = 1e-12,
    maxnumddmit: int = 500,
    relerrnltol: float = 1e-06,
    maxnumnlit: int = 100,
    project: bool = True,
    verbosity: int = 1,
) -> expression: ...
def predefinedlinearpoissonwalldistance(*args, **kwargs) -> Any: ...
def predefinedmagnetostaticforce(
    input: expressionlike, H: expressionlike, mu: expressionlike
) -> expression:
    """
    This function defines the weak formulation term for magnetostatic forces. The first argument ist the mechanical displacement test
    function or its gradient, the second is the magnetic field expression and the third argument is the magnetic permeability (
    must be a scalar).

    Let us call $\\boldsymbol{T}$  [$N/m^2$] the magnetostatic Maxwell stress tensor:
    $$
    \\boldsymbol{T} = \\mu \\ \\boldsymbol{H} \\otimes \\boldsymbol{H}
                        -
                    \\frac{1}{2} \\mu \\left( \\boldsymbol{H} \\cdot \\boldsymbol{H} \\right) \\ \\boldsymbol{I}
    $$
    where $\\mu$ is the magnetic permeability, $\\boldsymbol{H}$ is the magnetic field and $\\boldsymbol{I}$ is the identity matrix.
    The magnetostatic force density is $\\nabla \\cdot \\boldsymbol{T} [$N/m^3$]$ so that the loading for a mechanical problem can
    be obtained by adding the following term:
    $$
    \\int_{\\Omega} \\left( \\nabla \\cdot \\boldsymbol{T} \\right) \\cdot \\boldsymbol{u}^{\\prime} d\\Omega
    $$
    where $\\boldsymbol{u}$ is the mechanical displacement. The term can be rewritten in the form that is provided by this function:
    $$
    -\\int_{\\Omega} \\boldsymbol{T} \\ \\boldsymbol{\\epsilon}^{\\prime} d\\Omega
    $$
    where $\\boldsymbol{\\epsilon}$ is the infinitesimal strain tensor. This is identical to what is obtained using the virtual
    work principle. For details refer to *'Domain decomposition techniques for the nonlinear, steady state, finite element
    simulation of MEMS ultrasonic transducer arrays'*, page 40.

    In this function, a region should be provided to the test function argument to compute the force only for the degrees of
    freedom associated to that specific region (in the example below with *tf(u, top)* the force only acts on the surface region 'top'.
    In any case, a **correct force calculation requires including** in the integration domain all elements in the region where
    the force acts and in the **element layer around it** (in the example below 'vol' includes all volume elements touching
    surface 'top').

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; top=3
    >>> phi=field("h1"); u=field("h1xyz")
    >>> phi.setorder(vol,1)
    >>> u.setorder(vol,2)
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), 150e9, 0.3))
    >>> elasticity += integral(vol, predefinedelectrostaticforce(tf(u,top), -grad(phi), 4*getpi()*1e-7))

    See Also
    --------
    predefinedelectrostaticforce
    """
    return expression()

@overload
def predefinedmagnetostatics(
    dofa: expressionlike, tfa: expressionlike, nu: expressionlike, precondtype: str = ""
) -> tuple[expression, preconditioner]:
    """
    <<INTERNAL>>
    """

@overload
def predefinedmagnetostatics(
    dofa: expressionlike,
    tfa: expressionlike,
    a: expressionlike,
    nu: expressionlike,
    dhdb: expressionlike,
    precondtype: str = "",
) -> tuple[expression, preconditioner]: ...
def predefinedmagnetostatics(*args, **kwargs) -> Any: ...
def predefinednavierstokes(
    dofv: expressionlike,
    tfv: expressionlike,
    v: expressionlike,
    dofp: expressionlike,
    tfp: expressionlike,
    mu: expressionlike,
    rho: expressionlike,
    dtrho: expressionlike,
    gradrho: expressionlike,
    includetimederivs: bool = False,
    isdensityconstant: bool = True,
    isviscosityconstant: bool = True,
    precondtype: str = "",
) -> tuple[expression, preconditioner]:
    """
    This defines the weak formulation for the general (nonlinear) flow of Newtonian fluids:

    $$
    \\begin{cases}
      \\frac{\\partial \\rho}{\\partial t} + \\nabla \\cdot (\\rho \\ \\boldsymbol{v}) = 0 \\\\[5pt]
      \\rho \\left( \\frac{\\partial \\boldsymbol{v}}{\\partial t} + \\boldsymbol{v} \\cdot \\nabla \\boldsymbol{v} \\right) =
      - \\nabla p
      + \\nabla \\cdot \\left( \\mu \\left( \\nabla \\boldsymbol{v} + \\left( \\nabla \\boldsymbol{v} \\right)^T \\right)
      - \\frac{2}{3} \\mu \\left( \\nabla \\cdot \\boldsymbol{v} \\right) \\boldsymbol{I} \\right)
    \\end{cases}
    $$

    where,
    - $\\rho \\ [kg/m^3]$ is the fluid density
    - $\\mu \\ [Pa \\cdot s]$ is the dynamic viscosity of the fluid
    - $p \\ [Pa]$ is the pressure
    - $\\boldsymbol{v} \\ [m/s]$ is the flow velocity

    The formulation is provided in a form leading to a quadratic (Newton) convergence when solved iteratively in a loop. This
    formulation is only valid to simulate laminar as well as turbulent flows. Using it to simulate turbulent flows leads to a so-
    called **DNS** method (direct numerical simulation). DNS does not require any turbulence model since it takes into account the
    whole range of spatial and temporal scales of the turbulence. Therefore, it requires a spatial and time refinement that for
    industrial applications typically exceeds the computing power of the most advanced supercomputers. As an alternative, RANS and
    LES method can be used for turbulent flow simulation.

    The transition from a laminar to a turbulent flow is linked to a threshold value of the Reynolds number. For a flow in pipes
    typical Reynolds number below which the flow is laminar is about $2000$.

    Arguments `dtrho` and `gradrho` are respectively the time derivative and the gradient of the density while `includetimederivs`
    gives the option to include or not the time-derivative terms in the formulation. In case the density constant argument is set
    to True, the fluid is supposed incompressible and the Navier-Stokes equations are further simplified since the divergence of
    the velocity is zero. If the viscosity is constant **in space** (it does not have to be constant in time) the constant viscosity argument
    can be set to True. By default, the density and viscosity are supposed constant and the time-derivative terms are not included.
    Please note that to simulate the Stokes flow the **LBB condition has to be satisfied**. This is achieved by using nodal (h1)
    type shape functions with an interpolation order of at least one higher for the velocity field than for the pressure field.
    Alternatively, an additional isotropic diffusive term or other stabilization techniques can be used to overcome the LBB limitation.

    Example
    -------
    >>> mymesh = mesh("microvalve.msh")
    >>> fluid = 2   # physical region
    >>>
    >>> v=field("h1xy"); p=field("h1")
    >>> v.setorder(fluid, 2)
    >>> p.setorder(fluid, 1)    # Satisfies the LBB condition
    >>>
    >>> laminar = formulation()
    >>> laminar += integral(fluid, predefinednavierstokes(dof(v), tf(v), v, dof(p), tf(p), 8.9e-4, 1000, 0, 0))

    See Also
    --------
    predefinedstokes
    """
    return (expression(), preconditioner())

def predefinednavierstokescrosswindstabilization(
    dofv: expressionlike,
    tfv: expressionlike,
    v: expressionlike,
    p: expressionlike,
    diffusivity: expressionlike,
    rho: expressionlike,
    gradv: Sequence[expressionlike],
    vorder: int,
) -> expression:
    return expression()

def predefinednavierstokesstreamlinestabilization(
    dofv: expressionlike,
    tfv: expressionlike,
    v: expressionlike,
    dofp: expressionlike,
    tfp: expressionlike,
    diffusivity: expressionlike,
    rho: expressionlike,
    gradv: Sequence[expressionlike],
    vorder: int,
    pspg: bool,
    lsic: bool,
) -> expression:
    return expression()

@overload
def predefinednonlinearpoissonwalldistance(
    physreg: int,
    wallreg: int,
    poissonparameter: int,
    interpolationorder: int = 1,
    relresddmtol: float = 1e-12,
    maxnumddmit: int = 500,
    relerrnltol: float = 1e-06,
    maxnumnlit: int = 100,
    project: bool = True,
    verbosity: int = 1,
) -> expression:
    """
    This function calculates and returns distance values from the wall based on a generic p-Posison wall distance equation:

    $$
    \\begin{align*}
      \\nabla \\cdot (| \\nabla \\phi |^{p-2} \\ \\nabla \\phi) + 1 & = 0  \\qquad &on \\ \\ &\\Omega        \\\\[5pt]
      \\phi & = 0                               \\qquad &on \\ \\ &\\Gamma_u      \\\\[5pt]
      \\frac{d \\phi}{dn} & = 0                 \\qquad &on \\ \\ &\\Gamma_{N}
    \\end{align*}
    $$

    where $\\phi$ is the approximate wall distance function and $p$ is the Poisson parameter. The distance is calculated for the
    physical region *physreg* from the walls defined in *wallreg* argument. The Poisson parameter $p$ must be larger than or equal
    to 2. Higher the parameter better the distance field approximation. The term $|\\nabla \\phi|^{p-2}$ represents an apparent
    diffusion coefficient. When $p=2$, the equation reduces to the linear Poisson wall distance. See `predefinedlinearpoissonwalldistance`.

    More information can be found in *Wall-Distance Calculation for Turbulence Modelling, J. C. Bakker, Delft University of Technology.
    http://samofar.eu/wp-content/uploads/2018/10/Bakker_Jelle_BSc-thesis_2018.pdf .*

    The above system is non-linear and hence an iterative Newton solver is used. After calculating the distance function $\\phi$, a
    better approximation of distance is obtained as follows:

    $$
    d(\\phi) = -|\\nabla \\phi|^{p-1} + \\left( \\frac{p}{p-1} \\phi + |\\nabla \\phi|^p \\right)^{\\frac{p-1}{p}}
    $$

    This wall distance uses an above-zero limiter during calculation. Thus, to ensure that the distance value obtained is smooth,
    set the *project* argument to True. This will solve a projection of the distance values at the end and return a smooth solution.

    Example
    -------
    >>> mymesh = mesh("2D_Flatplate_35x25.msh")
    >>>
    >>> # physical regions
    >>> fluid=1, inlet=2, outlet=3, top=4, bot_upstream=5, plate=6
    >>>
    >>> nonlinearpoisson_wd = predefinednonlinearpoissonwalldistance(fluid, wall, p=4);

    See Also
    --------
    predefinedreciprocalwalldistance, predefinedlinearpoissonwalldistance
    """

@overload
def predefinednonlinearpoissonwalldistance(
    physreg: int,
    meshdeform: expressionlike,
    wallreg: int,
    poissonparameter: int,
    interpolationorder: int = 1,
    relresddmtol: float = 1e-12,
    maxnumddmit: int = 500,
    relerrnltol: float = 1e-06,
    maxnumnlit: int = 100,
    project: bool = True,
    verbosity: int = 1,
) -> expression: ...
def predefinednonlinearpoissonwalldistance(*args, **kwargs) -> Any: ...
@overload
def predefinedreciprocalwalldistance(
    physreg: int,
    wallreg: int,
    reflength: float,
    smoothpar: float = 0.5,
    interpolationorder: int = 1,
    relresddmtol: float = 1e-12,
    maxnumddmit: int = 500,
    relerrnltol: float = 1e-06,
    maxnumnlit: int = 100,
    verbosity: int = 1,
) -> expression:
    """
    This function calculates and returns distance values from the wall based on the reciprocal wall distance (G=1/d) equation:

    $$
    \\nabla \\cdot (G \\cdot \\nabla G) + (\\sigma - 1) \\ G(\\nabla \\cdot \\nabla G) - (1 + 2 \\sigma)G^4 = 0
    $$

    $$
    \\begin{align*}
      G & = \\frac{1}{L_{ref}} = G_{wall}                   \\qquad &on \\ \\ &\\Gamma_u      \\\\[5pt]
      \\frac{dG}{dn} & = 0                                  \\qquad &on \\ \\ &\\Gamma_{N}    \\\\[5pt]
      G_{init} & = [0 \\ .. \\ 1e-3] \\frac{1}{L_{ref}}   \\qquad &on \\ \\ &\\Omega
    \\end{align*}
    $$

    The distance is calculated for the physical region *physreg* from the walls defined in *wallreg* argument.

    More information can be found in *Fares, E., and W. Schröder. "A differential equation for approximate wall distance."
    International journal for numerical methods in fluids 39.8 (2002): 743-762.*

    **Excerpts from the above paper**:
    "The desired smoothing is controlled by the value of the smoothing parameter $\\sigma$. The larger the $\\sigma$ value means a
    stronger smoothing at sharp edges (but also a large deviation from exact distances). The value of the wall boundary condition
    $G_{wall}$ influences the smoothing too.

    Reference length $L_{ref}$ is relevant in the definition of the initial and boundary conditions. For geometries with just
    one-sided wall, $L_{ref}$ does not play a role- since the solution is the exact distance for all $\\sigma$ and $G_{wall}$.
    This formulation promises an enhancement of turbulence models at strongly curved surfaces."

    Smaller $\\sigma$ and larger $G_{wall}$ allow for better approximations of distances although at times it can be difficult
    to obtain convergence. In such cases, lowering the $G_{wall}$ improves.

    Example
    -------
    >>> mymesh = mesh("2D_Flatplate_35x25.msh")
    >>>
    >>> # physical regions
    >>> fluid=1, inlet=2, outlet=3, top=4, bot_upstream=5, plate=6
    >>>
    >>> reciprocal_wd = predefinedreciprocalwalldistance(fluid, wall, Lref=0.15);

    See Also
    --------
    predefinedlinearpoissonwalldistance, predefinednonlinearpoissonwalldistance
    """

@overload
def predefinedreciprocalwalldistance(
    physreg: int,
    meshdeform: expressionlike,
    wallreg: int,
    reflength: float,
    smoothpar: float = 0.5,
    interpolationorder: int = 1,
    relresddmtol: float = 1e-12,
    maxnumddmit: int = 500,
    relerrnltol: float = 1e-06,
    maxnumnlit: int = 100,
    verbosity: int = 1,
) -> expression: ...
def predefinedreciprocalwalldistance(*args, **kwargs) -> Any: ...
def predefinedslipwall(
    physreg: int,
    dofv: expressionlike,
    tfv: expressionlike,
    dofp: expressionlike,
    tfp: expressionlike,
    diffusivity: expressionlike,
    rho: expressionlike,
    vorder: int,
) -> expression:
    return expression()

def predefinedstabilization(
    stabtype: str,
    delta: expressionlike,
    f: expressionlike,
    v: expressionlike,
    diffusivity: expressionlike,
    residual: expressionlike,
) -> expression:
    """
    This function defines the isotropic, streamline anisotropic, crosswind, crosswind shockwave, streamline Petrov_Galerkin and 
    streamline upwind Petrov-Galerkin stabilization methods for the advection-diffusion problem:

    $$ 
    \\frac{\\partial c}{\\partial t} - \\nabla \\cdot (\\boldsymbol{\\alpha} \\nabla c) + \\nabla \\cdot (c \\boldsymbol{v}) = 0 
    $$

    where $c$ is the scalar quantity of interest, $\\boldsymbol{v} \\ [m/s]$ is the velocity that the quantity is moving with 
    and $\\boldsymbol{\\alpha} \\ [m^2/s]$ is the diffusivity tensor.

    A characteristic number of advection-diffusion problems is the Peclet number: 

    $$
    P_e = \\frac{\\text{diffusion time}}{\\text{advection time}} = \\frac{h \\ \\| v \\|}{\\alpha}
    $$

    where $h$ is the length of each mesh element. It quantifies the relative importance of advective and diffusive transport 
    rates. When the Peclet number is large ($P_e \\gg 1$) the problem is dominated by faster advection (higher advection 
    transport) and prone to spurious oscillations in the solution. Although lowering the Peclet number can be achieved by 
    refining the mesh, a classical alternative is to add stabilization terms to the original equation. A proper choice of 
    stabilization should remove oscillations while changing the original problem as little as possible. In the most simple 
    method proposed (isotropic diffusion), the diffusivity $\\alpha$ is artificially increased to lower the Peclet number. 
    The more advanced method proposed attempts to add artificial diffusion only where it is needed. In the crosswind shockwave, 
    SPG and SUPG methods the residual of the advection-diffusion equation is used to quantify the local amount of diffusion 
    to add. 
    The terms provided by the proposed stabilization methods have the following form:
    - isotropic diffusion: $\\delta \\ h \\ \\| \\boldsymbol{v} \\| \\ \\nabla c \\ \\nabla c^{\\prime}$
    - streamline anisotropic diffusion$: \\frac{\\delta \\ h}{\\| \\boldsymbol{v} \\|} 
    (\\boldsymbol{v} \\cdot \\nabla c) (\\boldsymbol{v} \\cdot \\nabla c^{\\prime})$
    - crosswind diffusion: $\\delta \\ h^{1.5} \\ (\\nabla c)^T \\ \\boldsymbol{T} \\ \\nabla c^{\\prime}$
    - crosswind shockwave: $\\frac{1}{2} \\ max(0, \\delta - \\frac{1}{\\gamma}) \\ h \\ \\frac{|residual|}{\\| \\nabla c \\|}
    (\\nabla c)^T \\ \\boldsymbol{T} \\ \\nabla c^{\\prime}, \\quad
    \\gamma = \\frac{\\| \\boldsymbol{v}_{\\parallel} \\|h}{2 \\alpha}, \\quad
    \\boldsymbol{v}_{\\parallel} = \\frac{\\boldsymbol{v} \\cdot \\nabla c}{\\| \\nabla c \\|^2} \\ \\nabla c$
    - streamline Petrov-Galerkin (SPG): $\\frac{\\delta \\ h}{\\| \\boldsymbol{v} \\|} \\ (residual) \\
    (\\boldsymbol{v} \\cdot \\nabla c^{\\prime})$
    - streamline upwind Petrov-Galerkin (SUPG): $\\lambda(\\lambda > 0) (residual) (\\boldsymbol{v} \\cdot \\nabla c^{\\prime}),
    \\quad \\lambda = \\frac{\\delta h}{\\| \\boldsymbol{v} \\|} - \\frac{\\alpha}{\\| \\boldsymbol{v} \\|^2}$

    where $c^{\\prime}$ is the test function associated with field $c$ and $\\boldsymbol{T} = \\mathbb{I} - 
    \\frac{1}{\\| v \\|^2} \\boldsymbol{v} \\otimes \\boldsymbol{v}$.

    To understand the effect of the crosswind diffusion one can notice that for a 2D flow in the $x$ direction only, tensor 
    $\\boldsymbol{T}$ becomes

    $$
        \\begin{bmatrix}
            1 & 0 \\\\
            0 & 1
        \\end{bmatrix}
        -
        \\begin{bmatrix}
            \\frac{v_x^2}{v_x^2} & 0 \\\\
            0 & 0
        \\end{bmatrix}
        -
        \\begin{bmatrix}
            0 & 0 \\\\
            0 & 1
        \\end{bmatrix}
    $$

    and the artificial diffusion is only added at places where $\\nabla c$ has a component in the direction perpendicular to 
    the flow.

    **How to use the predefined stabilization methods:**
    Due to the large amount of artificial diffusion added by the isotropic diffusion method it should only be considered as a 
    fallback option. In practice, a pair of one streamline and one crosswind method should be used with the smallest possible 
    tuning factor $\\delta$. If the problem allows, SUPG should be preferred over SPG and crosswind shockwave should be 
    preferred over the crosswind because the amount of diffusion added tends to be lower.

    Examples
    --------
    The different stabilization methods are defined for the following simulation setup:
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> c = field("h1")
    >>> v = field("h1xyz")
    >>> c.setorder(vol, 1)
    >>> v.setorder(vol, 1)
    >>> 
    >>> # Diffusivity alpha (can be a tensor)
    >>> alpha = expression(0.001)
    >>>
    >>> advdiff = formulation()
    >>> advdiff += integral(vol, predefinedadvectiondiffusion(dof(c), tf(c), v, alpha, 1.0, 1.0))
    >>>
    >>> # Tuning factor (stablization parameter)
    >>> delta = 0.5
    >>>
    >>> # isotropic diffusion
    >>> advdiff += integral(vol, predefinedstablization("iso", delta, c, v, 0.0, 0.0))
    >>>
    >>> # streamline anisotropic diffusion
    >>> advdiff += integral(vol, predefinedstabilization("aniso", delta, c, v, 0.0, 0.0))
    >>>
    >>> # crosswind diffusion
    >>> advdiff += integral(vol, predefinedstabilization("cw", delta, c, v, 0.0, 0.0))

    The following residual-based stabilizations require the strong-form residual. Neglecting the second-order space-derivative 
    still leads to a good residual approximation.
    >>> # The flow is supposed incompressible, i.e div(v) = 0
    >>> dofresidual = dt(dof(c)) + v*grad(dof(c))   # residual at current iteration
    >>> residual = dt(c) + v*grad(c)                # residual at previous iteration
    >>>
    >>> # crosswind shockwave diffusion: residual at previous iteration must be considered
    >>> advdiff += integral(vol, predefinedstabilization("cws", delta, c, v, alpha, residual))
    >>>
    >>> # streamline Petrov-Galerkin diffusion
    >>> advdiff += integral(vol, predefinedstabilization("spg", delta, c, v, alpha, dofresidual))
    >>>
    >>> # streamline upwind Petrov-Galerkin diffusion
    >>> advdiff += integral(vol, predefinedstabilization("supg", delta, c, v, alpha, dofresidual))
    """
    return expression()

def predefinedstabilizednavierstokes(
    dofv: expressionlike,
    tfv: expressionlike,
    v: expressionlike,
    dofp: expressionlike,
    tfp: expressionlike,
    p: expressionlike,
    mu: expressionlike,
    rho: expressionlike,
    dtrho: expressionlike,
    gradrho: expressionlike,
    includetimederivs: bool,
    isdensityconstant: bool,
    isviscosityconstant: bool,
    precondtype: str,
    supg: bool,
    pspg: bool,
    lsic: bool,
    cwnd: bool,
    vorder: int,
    gradv: Sequence[expressionlike],
) -> tuple[expression, preconditioner]:
    return (expression(), preconditioner())

def predefinedstokes(
    dofv: expressionlike,
    tfv: expressionlike,
    dofp: expressionlike,
    tfp: expressionlike,
    mu: expressionlike,
    rho: expressionlike,
    dtrho: expressionlike,
    gradrho: expressionlike,
    includetimederivs: bool = False,
    isdensityconstant: bool = True,
    isviscosityconstant: bool = True,
    precondtype: str = "",
) -> tuple[expression, preconditioner]:
    """
    This defines the weak formulation for the Stokes (**creeping**) flow, a linear form of Navier-Stokes where the advective term is
    ignored as the inertial forces are smaller compared to the viscous forces:

    $$
    \\begin{cases}
      \\frac{\\partial \\rho}{\\partial t} + \\nabla \\cdot (\\rho \\ \\boldsymbol{v}) = 0 \\\\[5pt]
      \\rho \\frac{\\partial \\boldsymbol{v}}{\\partial t} =
      - \\nabla p
      + \\nabla \\cdot \\left( \\mu \\left( \\nabla \\boldsymbol{v} + \\left( \\nabla \\boldsymbol{v} \\right)^T \\right)
      - \\frac{2}{3} \\mu \\left( \\nabla \\cdot \\boldsymbol{v} \\right) \\boldsymbol{I} \\right)
    \\end{cases}
    $$

    where,
    - $\\rho \\ [kg/m^3]$ is the fluid density
    - $\\mu \\ [Pa \\cdot s]$ is the dynamic viscosity of the fluid
    - $p \\ [Pa]$ is the pressure
    - $\\boldsymbol{v} \\ [m/s]$ is the flow velocity

    This formulation is only valid to simulate the flow of Newtonian fluids (air, water, ...) with a very small Reynolds number
    ($Re \\ll 1$):

    $$
    Re = \\frac{\\rho \\ v \\ L}{\\mu}
    $$

    where $L \\ [m]$ is the characteristic length of the flow. Low flow velocities, high viscosities or small dimensions can lead
    to a valid Stokes flow approximation. Flows in microscale devices such as microvalves are also good candidates for Stokes flow
    simulations.

    Arguments `dtrho` and `gradrho` are respectively the time derivative and the gradient of the density while `includetimederivs`
    gives the option to include or not the time-derivative terms in the formulation. In case the density constant argument is set
    to True, the fluid is supposed incompressible and the Navier-Stokes equations are further simplified since the divergence of
    the velocity is zero. If the viscosity **in space** (it does not have to be constant in time) the constant viscosity argument
    can be set to True. By default, the density and viscosity are supposed constant and the time-derivative terms are not included.
    Please note that to simulate the Stokes flow the **LBB condition has to be satisfied**. This is achieved by using nodal (h1)
    type shape functions with an interpolation order of at least one higher for the velocity field than for the pressure field.
    Alternatively, an additional isotropic diffusive term or other stabilization techniques can be used to over the LBB limitation.

    Example
    -------
    >>> mymesh = mesh("microvalve.msh")
    >>> fluid = 2   # physical region
    >>>
    >>> v=field("h1xy"); p=field("h1")
    >>> v.setorder(fluid, 2)
    >>> p.setorder(fluid, 1)    # Satisfies the LBB condition
    >>>
    >>> stokesflow = formulation()
    >>> stokesflow += integral(fluid, predefinedstokes(dof(v), tf(v), dof(p), tf(p), 8.9e-4, 1000, 0, 0))

    See Also
    --------
    predefinednavierstokes
    """
    return (expression(), preconditioner())

def predefinedstreamlinestabilizationparameter(
    v: expressionlike, diffusivity: expressionlike
) -> expression:
    return expression()

def predefinedturbulencecrosswindstabilization(
    v: expressionlike,
    rho: expressionlike,
    dofk: expressionlike,
    tfk: expressionlike,
    kp: expressionlike,
    gradk: expressionlike,
    productionk: expressionlike,
    dissipationknodof: expressionlike,
    diffusivityk: expressionlike,
    korder: int,
    dofepsomega: expressionlike,
    tfepsomega: expressionlike,
    epsomegap: expressionlike,
    gradepsomega: expressionlike,
    productionepsomega: expressionlike,
    dissipationepsomeganodof: expressionlike,
    diffusivityepsomega: expressionlike,
    epsomegaorder: int,
    fv1: expressionlike,
    cdkomega: expressionlike,
) -> expression:
    return expression()

def predefinedturbulencemodelsstkomega(
    v: expressionlike,
    rho: expressionlike,
    viscosity: expressionlike,
    walldistance: expressionlike,
    dofk: expressionlike,
    tfk: expressionlike,
    kp: expressionlike,
    gradk: expressionlike,
    korder: int,
    dofomega: expressionlike,
    tfomega: expressionlike,
    omegap: expressionlike,
    logomega: expressionlike,
    gradomega: expressionlike,
    omegaorder: int,
    stabsupgkomega: bool,
    stabcwdkomega: bool,
) -> expression:
    return expression()

def predefinedturbulencestreamlinestabilization(
    v: expressionlike,
    rho: expressionlike,
    dofk: expressionlike,
    tfk: expressionlike,
    gradk: expressionlike,
    productionk: expressionlike,
    dissipationk: expressionlike,
    diffusivityk: expressionlike,
    korder: int,
    dofepsomega: expressionlike,
    tfepsomega: expressionlike,
    gradepsomega: expressionlike,
    productionepsomega: expressionlike,
    dissipationepsomega: expressionlike,
    diffusivityepsomega: expressionlike,
    epsomegaorder: int,
    fv1: expressionlike,
    cdkomega: expressionlike,
) -> expression:
    return expression()

def predefinedviscoelasticity(
    dofu: expressionlike,
    tfu: expressionlike,
    u: field,
    Ep: expressionlike,
    nup: expressionlike,
    taup: expressionlike,
    physicalregion: int,
) -> expression:
    return expression()

def principalstresses(input: expressionlike) -> list[list[expression]]:
    """
    This returns the principal stresses and directions of a 3D symmetric stress tensor in Voigt form (6x1).
    The input can also be any other symmetric tensor (for example the strain tensor to obtain the principal strains).
    Returned values are [[$\\lambda_1, \\lambda_2, \\lambda_3$], [$v_1, v_2, v_3$]] where $\\lambda_i$ are the eigenvalues sorted descending and $v_i$ are the corresponding unit eigenvectors.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> u.setconstraint(sur)
    >>>
    >>> # Material properties
    >>> E = 150e9
    >>> nu = 0.3
    >>>
    >>> # Elasticity matrix for isotropic materials
    >>> H = expression(6,6, [1-nu,nu,nu,0,0,0, nu,1-nu,nu,0,0,0, nu,nu,1-nu,0,0,0, 0,0,0,0.5*(1-2*nu),0,0, 0,0,0,0,0.5*(1-2*nu),0, 0,0,0,0,0,0.5*(1-2*nu)])
    >>> H = H * E/((1+nu)*(1-2*nu))
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), H))
    >>>
    >>> # Atmospheric pressure load (volumetric force) on top face deformed by field u (might require a nonlinear iteration)
    >>> elasticity += integral(top, u, -normal(vol)*1e5 * tf(u))
    >>>
    >>> elasticity.solve()
    >>>
    >>> cauchystress = H * strain(u)
    >>> ps = principalstresses(cauchystress)
    >>>
    >>> maxps = ps[0][0]
    >>> maxpdir = ps[1][0]
    >>> maxps.write(vol, "maxps.vtk", 1)
    >>> maxpdir.write(vol, "maxpdir.vtk", 1)
    >>> maxpsmaxval = maxps.max(vol, 5)[0]
    >>> maxpsmaxval

    See Also
    --------
    vonmises
    """
    ...

def printonrank(rank: int, toprint: str) -> None:
    """
    This function allows the string argument `toprint` to be printed only by the given `rank` number. This is useful
    during DDM simulations and the user wants to print a custom output to monitor the simulation. If the python built-in print
    function is used while running DDM simulations, then the input string will be printed by all the ranks resulting in
    the same text written multiple times.

    Example
    -------
    >>> ...
    >>> Uz_max = abs(qs.compz(fld.u)).allmax(reg.solidmechanics_target, 5)[0] * 1e6
    >>>
    >>> # Assuming a DDM simulation is run on 4 nodes (ranks)
    >>> # 1) The following is printed by all the ranks (so, it will be printed 4 times)
    >>> print(f"Max. Z-deflection is {Uz_max} microns", flush=True)
    >>>
    >>> # 2) Alternatively, the following can be used to print the string only from a certain rank
    >>> if (getrank() == 0):
    >>>     # below text is printed only by rank 0
    >>>     print(f"Max. Z-deflection is {Uz_max} microns", flush=True)
    >>>
    >>> # 3) Same as the second case, but achieved in a single line
    >>> printonrank(0, f"Max. Z-deflection is {Uz_max} microns")
    """
    ...

def printphysicalram() -> None: ...
def printsparameters(Sparams: Sequence[Sequence[float]]) -> None:
    """
    Prints the magnitudes (unit: dB) and angles (unit: degrees) of the S-parameters returned by allcomputesparameters.

    See Also
    --------
    allcomputesparameters
    """
    ...

@overload
def printtotalforce(
    physreg: int,
    EorH: expressionlike,
    epsilonormu: expressionlike,
    extraintegrationorder: int = 0,
) -> list[float]:
    """
    This prints the total force and its unit. The total force value is returned.

    Examples
    --------
    **Example 1**: `printtotalforce(physreg:int, EorH:expression, epsilonormu:expression, extraintegrationorder:int=0)`
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> phi = field("h1")
    >>> phi.setorder(vol, 2)
    >>>
    >>> mu0 = 4 * getpi() * 1e-7
    >>> mu = parameter()
    >>> mu.setvalue(vol, mu0)
    >>> printtotalforce(vol, -grad(phi), mu)

    **Example 2**: `printtotalforce(physreg:int, meshdeform:expression, EorH:expression, epsilonormu:expression, extraintegrationorder:int=0)`

    This is similar to the above function but the total force is computed and returned on the mesh deformed by the field `u`.
    >>> ...
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> printtotalforce(vol, u, -grad(phi), mu)

    See Also
    --------
    gettotalforce
    """

@overload
def printtotalforce(
    physreg: int,
    meshdeform: expressionlike,
    EorH: expressionlike,
    epsilonormu: expressionlike,
    extraintegrationorder: int = 0,
) -> list[float]: ...
def printtotalforce(*args, **kwargs) -> Any: ...
@overload
def printvector(input: Sequence[float]) -> None:
    """
    This prints the `input` list as well as its values. The `input` can be a list of double/int/bool elements.

    Example
    -------
    >>> v = [2.4, 3.14, -0.1]
    >>> printvector(v)
    Vector size is 3
    2.4 3.14 -0.1

    See Also
    --------
    loadvector, writevector
    """

@overload
def printvector(input: Sequence[int]) -> None: ...
@overload
def printvector(input: Sequence[bool]) -> None: ...
def printvector(*args, **kwargs) -> Any: ...
def printversion() -> None: ...
def pulse(
    uptime: expressionlike, downtime: expressionlike, delay: expressionlike
) -> expression:
    """
    This function creates a single rectangular pulse signal. The signal starts at value 1 and stays there for `uptime` seconds.
    Then it drops back to value 0 and stays there for `pulsedowntime` seconds, after which it remains at 0 forever.

    If the `delay>0`, the signal is initially at value 0. Then at `0 + delay` seconds the signal jumps to value 1
    and stays there for `uptime` seconds. The value of the signal drops back to value 0 and stays there for `downtime` seconds,
    after which it remains at 0 forever.

    In the pulse signal, the jumps or drops in the value occurs within a single timestep. This is contrast to the ramp signal where
    the ramp-up or ramp-down occurs over a number of timesteps specified by the respective ramp-up and ramp-down time.

    ![generalramp](./imagesAPI/pulsefunction.svg)

    Example
    -------
    The below example creates a pulse signal which starts at 1s (due to the delay=1), stays at value 1 for 5s and then remains
    0 for the rest of the time.
    >>> Q = 15 * qs.pulse(uptime=5, downtime=2, delay=1)

    See Also
    --------
    pulses, ramp, ramps
    """
    return expression()

def pulses(
    uptime: expressionlike,
    downtime: expressionlike,
    delay: expressionlike,
    repeats: expressionlike,
) -> expression:
    """
    This function creates a repeating rectangular pulse signal that cycles through the same pattern multiple times.
    Each cycle of the pulse signal consists of
    - a high phase during which the signal stays at value 1 for `uptime` seconds,
    - followed by a low phase during which the signal stays at value 0 for `downtime` seconds, and,
    - for the remaining duration of the time period, the signal continues to remain at 0.

    If the `delay>0`, the signal is initially at value 0 and the pulse starts only after `0 + delay` seconds.
    Note that the delay is not part of the pulse cycle and hence occurs only at the beginning of the pulse signal
    and is **not** repeated for each cycle.

    The time period of each pulse cycle is `uptime + downtime`. The cycle repeats after every time period
    for the specified number of `repeats`. If `repeats` is set to -1, the cycle repeats indefinitely.

    ![generalramp](./imagesAPI/pulsesfunction.svg)

    Example
    -------
    The below example creates a pulse signal which starts at 1s (due to the delay=1), stays at value 1 for 5s, drops to
    0 and stays at this value for 2s and repeats this pattern for a total of 3 cycles.
    >>> Q = 15 * qs.pulses(uptime=5, downtime=2, delay=1, repeats=3)

    See Also
    --------
    pulse, ramp, ramps
    """
    return expression()

def qtoalpha(freq: expressionlike, q: expressionlike) -> expression:
    """
        This function converts the given frequency `freq`and $Q$-factor `q` to a Rayleigh damping parameter $\\alpha$, which is the
        mass-proportional damping coefficient [*1/seconds*].
    $$
        \\alpha = \\dfrac{\\omega}{2Q} = \\dfrac{\\pi f}{Q}
    $$

    Example
    -------
    >>> qs.qtoalpha(freq=1e6, q=1000)

    See Also
    --------
    qtobeta
    """
    return expression()

def qtobeta(freq: expressionlike, q: expressionlike) -> expression:
    """
        This function converts the given frequency `freq`and $Q$-factor `q` to a Rayleigh damping parameter $\\beta$, which is the
        stiffness-proportional damping coefficient [*seconds*].
    $$
        \\beta = \\frac{1}{2 \\omega Q} = \\frac{1}{4 \\pi f Q}
    $$

    Example
    -------
    >>> qs.qtobeta(freq=1e6, q=1000)

    See Also
    --------
    qtoalpha
    """
    return expression()

def ramp(
    rampuptime: expressionlike,
    holdtime: expressionlike,
    rampdowntime: expressionlike,
    delay: expressionlike,
) -> expression:
    """
    This creates a single ramp signal. It is a signal that starts initially at value 0. Then at `0 + delay` seconds it transitions
    from value 0 to 1 in a linear increase. That transition happens in `rampuptime` seconds. This is followed by a flat value 1
    that is held for `holdtime` seconds. This is followed by a linear decrease from value 1 to 0 that happens in `rampdowntime` seconds.
    The value is then forever 0 after that.

    The `rampuptime` is the time to transition linearly from value 0 to 1. The `holdtime` is the time
    the value stays at 1. The `rampdowntime` is the time to transition linearly from value 1 to 0. The `delay` is the time at which
    the rampup starts.

    ![generalramp](./imagesAPI/rampfunction.svg)

    Examples
    --------
    The operation current is ramped from 0 to 200 in 3 seconds and is held at 200 for another 5 seconds after which it is ramped down to
    0 in the next 3 seconds.
    >>> # Operation current
    >>> Iop = 200 * ramp(rampuptime=3, holdtime=5, rampdowntime=3, delay=0)

    If the `holdtime` is set to zero, then the ramp defines a triangular function.
    >>> Iop = 200 * ramp(rampuptime=3, holdtime=0, rampdowntime=3, delay=0)

    If the `rampuptime` and `rampdowntime` is set zero with a positive `holdtime`, then a rectangular function is defined.
    >>> Iop = 200 * ramp(rampuptime=0, holdtime=5, rampdowntime=0, delay=0)

    See Also
    --------
    ramps, pulse, pulses
    """
    return expression()

def ramps(
    rampuptime: expressionlike,
    holdtime: expressionlike,
    rampdowntime: expressionlike,
    delay: expressionlike,
    period: expressionlike,
    repeats: expressionlike,
) -> expression:
    """
    This function creates a repeating ramp signal that cycles through the same pattern multiple times.
    Each cycle of the ramp signal consists of
    - a ramp-up phase during which the signal linearly transitions from 0 to 1 in `rampuptime` seconds,
    - a hold phase during which the signal is at a constant value of 1 for `holdtime` seconds,
    - a ramp-down phase during which the signal linearly transitions from 1 to 0 in `rampdown` seconds, and,
    - for the remaining duration of the time period, the signal remains at 0.

    If the `delay>0`, the signal is initially at value 0 and the rampup starts only after `0 + delay` seconds.
    Note that the delay is not part of the ramp cycle and hence occurs only at the beginning of the ramp signal
    and is **not** repeated for each cycle.

    The argument `period` specifies the time period of the ramp signal cycle. The cycle repeats after every
    `period` seconds for the specified number of `repeats`. If `repeats` is set to -1, the cycle repeats indefinitely.

    ![generalramp](./imagesAPI/rampsfunction.svg)

    Example
    -------
    The below example creates a ramp signal that starts at t=1s, takes 2s to ramp-up, holds for 3s, takes 2s to ramp-down, and
    repeats this pattern every 10s for a total of 2 cycles.
    >>> # Heat source
    >>> Q = 15 * qs.ramp(rampuptime=2, holdtime=3, rampdowntime=2, delay=1, period=10, repeats=2)

    Note that the total duration of one ramp cycle (`rampuptime + holdtime + rampdowntime`) must typically be less than or
    equal to the `period` to avoid overlapping cycles. The consistency of the ramp signal with overlapping cycles is not
    guaranteed.

    See Also
    --------
    ramp, pulse, pulses
    """
    return expression()

def realZ(V: expressionlike, I: expressionlike) -> float:
    """
    This returns an expression that is the real part of the Z = V/I complex impedance.

    See Also
    --------
    imagZ, absZ, argZ
    """
    ...

@overload
def receive(source: int, tag: int, data: Sequence[int]) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def receive(source: int, tag: int, data: Sequence[float]) -> None: ...
def receive(*args, **kwargs) -> Any: ...
def rectangularport(
    portphysreg: int,
    modetype: str,
    mmode: int,
    nmode: int,
    mu: expressionlike,
    eps: expressionlike,
    cxynodecoords: Sequence[Sequence[float]],
    integrationorder: int = 5,
) -> list[expression]:
    """
    This function returns the TE or TM mode of index $(m, n)$ (according to the parameters `mmode` and `nmode`) for the rectangular waveguide whose cross section $S$ is the physical region `portphysreg`.
    The parameter `modetype` should be "te" or "tm". The material parameters $\\mu$ and $\\epsilon$ are required as input arguments; these must be real and scalar-valued.
    The list `cxynodecoords` should contain three corner points of the rectangular cross section; `cxynodecoords[1] - cxynodecoords[0]` gives the $x$-direction and `cxynodecoords[2] - cxynodecoords[0]` the $y$-direction.

    The mode is returned as a list of expressions containing the fields $E$ and $H$ (both real-valued) and the phase constant $\\beta$.
    The mode is scaled such that the power into the waveguide equals one watt; `integrationorder` determines the order of the integration rule used to compute the power.

    Example
    -------
    >>> qs.setfundamentalfrequency(4.77135e10)
    >>> te01 = qs.rectangularport(rectangular_crosssection, "te", 0, 1, qs.getmu0(), 2.5 * qs.getepsilon0(), [[-0.0015, -0.001, 0.008], [-0.0015, 0.001, 0.008], [0.0015, -0.001, 0.008]])
    >>> te01[0].write(rectangular_crosssection, 'Ereal.vtu', 2)
    >>> te01[1].write(rectangular_crosssection, 'Hreal.vtu', 2)
    >>> te01[2].evaluate()
    1184.644402984432

    See Also
    --------
    alleigenport
    """
    ...

def rhocpcstoH(
    rho: expressionlike, cp: expressionlike, cs: expressionlike
) -> expression:
    return expression()

def rhodofj(sigma: parameter, j: expressionlike, dofj: expressionlike) -> expression:
    return expression()

def rotate(
    expr: expressionlike,
    ax: float,
    ay: float,
    az: float,
    leftop: str = "default",
    rightop: str = "default",
) -> expression:
    return expression()

@overload
def scatter(scatterer: int, toscatter: Sequence[int], fragment: Sequence[int]) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def scatter(
    scatterer: int, toscatter: Sequence[float], fragment: Sequence[float]
) -> None: ...
@overload
def scatter(
    scatterer: int,
    toscatter: Sequence[int],
    fragment: Sequence[int],
    fragsizes: Sequence[int],
) -> None: ...
@overload
def scatter(
    scatterer: int,
    toscatter: Sequence[float],
    fragment: Sequence[float],
    fragsizes: Sequence[int],
) -> None: ...
def scatter(*args, **kwargs) -> Any: ...
def scatterwrite(
    filename: str,
    xcoords: Sequence[float],
    ycoords: Sequence[float],
    zcoords: Sequence[float],
    compxevals: Sequence[float],
    compyevals: Sequence[float] = [],
    compzevals: Sequence[float] = [],
) -> None:
    """
    This writes to the output file a scalar or vector values at given coordinates. If atleast one of the `compyevals` or
    `compzevals` is not empty then the values saved are vectors and not scalars. For scalars, only `compxevals` must be provided.
    If the length of all the list arguments are not identical, a RuntimeError is raised.

    Example
    -------
    >>> Define coordinates of three points: (0.0,0.0,0.0), (1.0,1.0,0.0) and (2.0,2.0,0.0)
    >>> coordx = [0.0, 1.0, 2.0]
    >>> coordy = [0.0, 1.0, 2.0]
    >>> coordz = [0.0, 0.0, 0.0]
    >>>
    >>> vals = [10, 20, 30]
    >>> scatterwrite("scalarvalues.vtk", coordx, coordy, coordz, vals)
    >>>
    >>> xvals = [10, 20, 30]
    >>> yvals = [40, 50, 60]
    >>> scatterwrite("vectorvalues.vtk", coordx, coordy, coordz, xvals, yvals)
    """
    ...

def selectall() -> int:
    """
    This returns a new or an existing physical region that covers the entire domain.

    Example
    -------
    >>> rega = 1; regb = 2
    >>> qa = shape("quadrangle", rega, {0,0,0, 1,0,0, 1,1,0, 0,1,0}, {5,5,5,5})
    >>> qb = shape("quadrangle", regb, {1,0,0, 2,0,0, 2,1,0, 1,1,0}, {5,5,5,5})
    >>> mymesh = mesh([qa, qb])
    >>> wholedomain = selectall()
    >>> mymesh.write("mesh.msh")

    See Also
    --------
    selectunion, selectintersection, selectnooverlap, `shape`, `mesh`
    """
    ...

def selectintersection(physregs: Sequence[int], intersectdim: int) -> int:
    """
    This returns a new or an existing physical region that is the intersection of physical regions passed via the argument
    `physregs`. The `intersectdim` argument determines the dimensional data from the intersection that would be utilized
    in subsequent operations such as setting constraints on a physical region or writing a field or expression to the
    physical region. For,
    * `intersectdim=3`: from the intersection, only volumes are used in subsequent operations.
    * `intersectdim=2`: from the intersection, only surfaces are used in subsequent operations.
    * `intersectdim=1`: from the intersection, only lines are is used in subsequent operations.
    * `intersectdim=0`: from the intersection, only points are is used in subsequent operations.

    This is useful in isolating only those dimensional data that might be necessary and ignoring the others arising
    from the intersection. Note that, the intersected region itself is not affected by `intersectdim`. This argument
    only determines which dimensional data is utilized when the intersected physical region is used in calculations or
    operations.

    Examples
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3              # physical regions
    >>>
    >>> # Influence of `intersectdim`
    >>> intersectdim = 3
    >>> intersectedreg = selectintersection([vol, vol], intersectdim)
    >>> expression(1).write(intersectedreg, "out_3D.vtk", 1)    # uses only volume from the intersectedreg
    >>>
    >>> intersectdim = 2
    >>> intersectedreg = selectintersection([vol, vol], intersectdim)
    >>> expression(1).write(intersectedreg, "out_2D.vtk", 1)    # uses only surfaces from the intersectedreg
    >>>
    >>> intersectdim = 1
    >>> intersectedreg = selectintersection([vol, vol], intersectdim)
    >>> expression(1).write(intersectedreg, "out_1D.vtk", 1)    # uses only lines from the intersectedreg
    >>>
    >>> intersectdim = 0
    >>> intersectedreg = selectintersection([vol, vol], intersectdim)
    >>> expression(1).write(intersectedreg, "out_0D.vtk", 1)    # uses only points from the intersectedreg

    See Also
    --------
    selectunion, selectall, selectnooverlap
    """
    ...

def selectnooverlap() -> int:
    """
    This returns a new or an existing physical region that covers no-overlap domain in case of overlap DDM and the entire domain otherwise.

    See Also
    --------
    selectunion, selectintersection, selectall
    """
    ...

def selectunion(physregs: Sequence[int]) -> int:
    """
    This returns a new or an existing physical region that is the union of physical regions passed via the argument `physregs`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> sur=2; top=3                    # physical regions
    >>> surandtop = selectunion([2,3])  # unioned physical region

    See Also
    --------
    selectintersection, selectall, selectnooverlap
    """
    ...

@overload
def send(destination: int, tag: int, data: Sequence[int]) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def send(destination: int, tag: int, data: Sequence[float]) -> None: ...
def send(*args, **kwargs) -> Any: ...
def setaxisymmetry() -> None:
    """
    This call should be placed at the very beginning of the code. After the call everything will be solved assuming axisymmetry
    (works for 2D meshes in the xy plane only). All equations should be written in their 3D form.

    In order to correctly take into account the cylindrical coordinate change, the appropriate space derivative
    operators should be used. For example, the *gradient of a vector* operator required in the mechanical strain calculation to
    compute the gradient of mechanical displacement should not be defined manually using `dx`, `dy` and `dz` space derivatives.
    The `grad` operator should instead be called on the mechanical displacement vector. Note that If the function is called after
    loading a mesh, a RuntimeError is raised.

    Example
    -------
    >>> setaxisymmetry()
    """
    ...

def setdata(invec: vec) -> None:
    """
    This function transfers the vector data to all fields and ports defined in the formulation associated to the vector.
    If the formulation uses ports, then this method must be used to update port values from the solution vector.
    Using `field.setdata` only updates the fields.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1"); w = field("h1")
    >>> v.setorder(vol, 1)
    >>>
    >>> projection = formulation()
    >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))
    >>> projection.generate()
    >>> sol = solve(projection.A(), projection.b()) # returns the solution vector
    >>>
    >>> # set the data
    >>> v.setdata(vol, sol) # sets only the field `v`
    >>> # or
    >>> setdata(sol) # set all fields including ports associated with `sol` vector

    See Also
    --------
    field.setdata
    """
    ...

@overload
def setextrapolationsymmetry(symplanes: Sequence[Sequence[float]]) -> None: ...
@overload
def setextrapolationsymmetry(
    xequal0sym: bool, yequal0sym: bool, zequal0sym: bool
) -> None: ...
def setextrapolationsymmetry(*args, **kwargs) -> Any: ...
def setfundamentalfrequency(f: float) -> None:
    """
    This defines the fundamental frequency (in $Hz$) required for multi-harmonic problems.

    Example
    -------
    >>> setfundamentalfrequency(50)
    """
    ...

def setmaxnumthreads(mnt: int) -> None:
    """
    <<INTERNAL>>
    Sets the maximum number of threads allowed to input value `mnt`.

    Example
    -------
    >>> setmaxnumthreads(2)
    >>> mnt = getmaxnumthreads()
    2

    See Also
    --------
    getmaxnumthreads
    """
    ...

def setphysicalregionshift(shiftamount: int) -> None:
    """
    This shifts the physical region numbers by `shiftamount` x (1 + physical region dimension) when loading a mesh.

    Example
    -------
    In the example the point/line/face/volume (0D/1D/2D/3D) physical region numbers will be shifted by 1000/2000/3000/4000 when
    a mesh is loaded.
    >>> setphysicalregionshift(1000)
    """
    ...

def settime(t: float) -> None:
    """
    This sets the time variable *t*.

    Example
    -------
    >>> settime(1e-3)

    See Also
    --------
    gettime, t
    """
    ...

@overload
def settimederivative(dtx: vec) -> None:
    """
    This allows us to set the time derivative vectors to the corresponnding fields used in the formulation.

    Examples
    --------
    **Example 1**: `settimederivative(dtx:vec)`

    This sets the first-order time derivate vector and removes the second-order time derivative vector.
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>> v.setconstraint(sur)
    >>>
    >>> poisson = formulation()
    >>> poisson += integral(vol, grad(dof(v))*grad(tf(v)))
    >>> solt1=vec(poisson); solt2=vec(poisson)
    >>> dtsol = 0.1 * (solt2 - solt1)
    >>> settimederivative(dtsol)
    >>> dt(v).write(vol, "dtv.pos", 1)

    **Example 2**: `settimederivative(dtx:vec, dtdtx:vec)`

    This sets the first and second-order time derivative vectors.
    >>> ...
    >>> settimederivative(dtsol, vec(poisson))
    >>> dtdt(v).write(vol, "dtdtv.pos", 1)
    """

@overload
def settimederivative(dtx: vec, dtdtx: vec) -> None: ...
def settimederivative(*args, **kwargs) -> Any: ...
def shearviscosity(
    freq: expressionlike,
    rho: expressionlike,
    E: expressionlike,
    nu: expressionlike,
    dbpmpmhzS: expressionlike,
) -> expression:
    """
    This functions returns the shear viscosity ($Pa \\cdot s$) of the elastic medium for the given attenuation coefficient and
    target frequency.
    The arguments `rho`, `E`, `nu` are respectively the density, Young's modulus, Poisson's ratio of the elastic medium which is
    used to calculate the speed of the S-wave.
    The argument `dbpmpmhzS` is the **shear** attenuation coefficient and must be provided in ($dB/m/MHz$).
    The conversion from ($dB/m/MHz$) to into ($Neper/m/MHz$) is taken care automatically in the function definition.

    The `freq` argument is the target frequency for the damping model with a linear relationship between frequency and damping.

    The shear viscosity is given by
    $$
        \\nu_s = \\frac{2 \\alpha_s \\rho {v_s}^3 \\omega} {\\omega_{ref}^3} \\\\[10pt]
        v_s = \\sqrt{\\frac{E}{2\\rho (1+\\nu)}} \\\\[10pt]
        \\omega_{target} = 2 \\pi f \\qquad ; \\qquad
        \\omega_{ref} = 2 \\pi \\times 10^6
    $$

    where,
    - $\\nu_s$ is the shear viscosity ($Pa \\cdot s$),
    - $\\alpha_s$ is the shear attenuation coefficient ($Neper/m/MHz$),
    - $v_s$ is the speed of S-wave ($m/s$),
    - $E$ is the Young's modulus ($Pa$),
    - $\\nu$ is the Poisson's ratio,
    - $\\rho$ is the density ($kg/m^3$),
    - $\\omega_{target}$ is target angular frequency ($rad/s$),
    - $\\omega_{ref}$ is the reference angular frequency ($rad/s$, corresponding to $1 \\, MHz$), and,
    - $f$ is target wave frequency ($Hz$).

    See Also
    --------
    shearviscosityfromv, bulkviscosity, bulkviscosityfromv
    """
    return expression()

def shearviscosityfromv(
    freq: expressionlike,
    rho: expressionlike,
    vs: expressionlike,
    dbpmpmhzS: expressionlike,
) -> expression:
    """
    This functions returns the shear viscosity ($Pa \\cdot s$) of the elastic medium for the given attenuation coefficient and
    target frequency.
    The argument `rho` is the density of the elastic medium.
    The arguments `vs` correspond to the speed of S-wave in the medium.
    The argument `dbpmpmhzS` is the **shear** attenuation coefficient and must be provided in ($dB/m/MHz$).
    The conversion from ($dB/m/MHz$) to into ($Neper/m/MHz$) is taken care automatically in the function definition.

    The `freq` argument is the target frequency for the damping model with a linear relationship between frequency and damping.

    The shear viscosity is given by
    $$
        \\nu_s = \\frac{2 \\alpha_s \\rho {v_s}^3 \\omega} {\\omega_{ref}^3} \\\\[10pt]
        \\omega_{target} = 2 \\pi f \\qquad ; \\qquad
        \\omega_{ref} = 2 \\pi \\times 10^6
    $$

    where,
    - $\\nu_s$ is the shear viscosity ($Pa \\cdot s$),
    - $\\alpha_s$ is the shear attenuation coefficient ($Neper/m/MHz$),
    - $v_s$ is the speed of S-wave ($m/s$),
    - $\\rho$ is the density ($kg/m^3$),
    - $\\omega_{target}$ is target angular frequency ($rad/s$),
    - $\\omega_{ref}$ is the reference angular frequency ($rad/s$, corresponding to $1 \\, MHz$), and,
    - $f$ is target wave frequency ($Hz$).

    See Also
    --------
    shearviscosity, bulkviscosity, bulkviscosityfromv
    """
    return expression()

def sin(input: expressionlike) -> expression:
    """
    This returns an expression that is the $sin$ of input. The input expression is in `radians`.

    Example
    -------
    >>> expr = sin(getpi()/2)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    1
    >>>
    >>> expr = sin(2)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    0.909297

    See Also
    --------
    cos, tan, asin, acos, atan
    """
    return expression()

def skindepth(sigma: expressionlike, mu: expressionlike) -> expression:
    return expression()

def sn(n: float) -> expression:
    """
    This function takes as an argument the fundamental frequency multiplier. It is a shortform for $sin(n * 2\\pi f t)$.

    Example
    -------
    >>> f = 15.5 * 1e+9  # fundamnetal frequency
    >>> setfundamentalfrequency(f)
    >>> drivingsignal = sn(2)  # same as sin(n* 2*getpi*f*t())

    See Also
    --------
    cn
    """
    return expression()

@overload
def solve(A: mat, b: vec, soltype: str = "lu") -> vec:
    """
    This function solves an algebraic problem. This function can solve both nonlinear and linear systems. Nonlinear problems are
    solved with a fixed-point iteration. Linear problems can be solved with both direct and iterative solvers. Depending on the
    algebraic problem and the solver needed, the overloaded solve function can be called with different numbers and types of
    arguments as shown in the examples below.

    Examples
    --------
    **Example 1**: `solve(A:mat, b:vec, soltype:str="lu", diagscaling:bool=False) -> quanscient.vec`

    This solves a linear algebraic problem with a (possibly reused) LU or Cholesky factorization by calling the mumps parallel
    direct solver via PETSC. The matrix can be diagonally scaled for improved conditioning (especially in multiphysics
    problems). In the case of diagonal scaling the matrix $A$ is modified after the call.
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2
    >>>
    >>> v=field("h1"); x=field("x")
    >>> v.setorder(vol, 1)
    >>>
    >>> projection = formulation()
    >>> projection += integral(vol, dof(v)*tf(v) - x*tf(v)) # linear system
    >>>
    >>> projection.generate()
    >>> sol = solve(projection.A(), projection.b()) # mumps direct solver

    **Example 2**: `solve(A:mat, b:List[vec], soltype:str="lu") -> List[vec]`

    This is same as the previous example but allows us to efficiently solve $Ax = b$ for multiple right-hand side vectors $b$.
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2
    >>>
    >>> v=field("h1"); x=field("x")
    >>> v.setorder(vol, 1)
    >>>
    >>> projection = formulation()
    >>> projection += integral(vol, (dof(v) - x)*tf(v)) # linear system
    >>>
    >>> projection.generate()
    >>> b0 = projection.b()
    >>> b1 = 2 * b0
    >>> b2 = 3 * b0
    >>>
    >>> sol = solve(projection.A(), [b0, b1, b2]) # mumps direct solver
    >>>
    >>> # solution for b0
    >>> v.setdata(vol, sol[0])
    >>> v.write(vol, "sol0.pos", 1)
    >>>
    >>> # solution for b1
    >>> v.setdata(vol, sol[1])
    >>> v.write(vol, "sol1.pos", 1)
    >>>
    >>> # solution for b2
    >>> v.setdata(vol, sol[2])
    >>> v.write(vol, "sol2.pos", 1)

    **Example 3**: `solve(A:mat, b:vec, sol:vec, relrestol:double, maxnumit:int, soltype:str="bicgstab", precondtype:str="sor", verbosity:int=1, diagscaling:bool=False)`

    This solves a linear algebraic problem with a preconditioned *(ilu, sor, gamg)* iterative solver *(gmres or bicgstab)*. Vector
    *sol* is used as an initial guess and holds the solution at the end of the call. Values *relrestol* and *maxnumit* give the
    relative residual tolerance and the maximum number of iterations to be performed by the iterative solver. The matrix can be
    diagonally scaled for improved conditioning (especially in multiphysics problems). In the case of diagonal scaling the matrix
    $A$ is modified after the call.
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2
    >>>
    >>> v=field("h1"); x=field("x")
    >>> v.setorder(vol, 1)
    >>>
    >>> projection = formulation()
    >>> projection += integral(vol, dof(v)*tf(v) - x*tf(v)) # linear system
    >>>
    >>> projection.generate()
    >>>
    >>> initsol = vec(projection)
    >>> solve(projection.A(), projection.b(), initsol, 1e-8, 200) # iterative solver
    >>> v.setdata(vol, initsol)
    >>> print(f"Max solution value is {v.max(vol, 5)[0]}")
    Max solution value is 1.013415

    **Example 4**: `solve(nltol:double, maxnumnlit:int, realxvalue:double, formuls:List[formulation], verbosity:int=1) -> int`

    This solves a nonlinear problem with a fixed point iteration. A relaxation value can be provided with `relaxvalue` argument.
    Usually, a relaxation value less than $1.0$ (under-relaxation) is used to avoid divergence of a solution.
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2
    >>>
    >>> v=field("h1");
    >>> v.setorder(vol, 1)
    >>> v.setconstraint(sur, 0)
    >>>
    >>> electrostatics = formulation()
    >>> electrostatics += integral(vol, grad(dof(v))*grad(tf(v)) + v*tf(v) )
    >>>
    >>> solve(1e-4, 100, 1.0, [electrostatics])

    See Also
    --------
    allsolve, formulation.allsolve
    """

@overload
def solve(A: mat, b: Sequence[vec], soltype: str = "lu") -> list[vec]: ...
@overload
def solve(
    A: mat,
    b: vec,
    sol: vec,
    relrestol: float,
    maxnumit: int,
    soltype: str = "gmres",
    precondtype: str = "sor",
    verbosity: int = 1,
) -> None: ...
@overload
def solve(
    nltol: float,
    maxnumnlit: int,
    relaxvalue: float,
    formuls: Sequence[formulation],
    verbosity: int = 1,
) -> int: ...
def solve(*args, **kwargs) -> Any: ...
def sqrt(input: expressionlike) -> expression:
    """
    This returns an expression that is the square root of the input expression.

    Example
    -------
    >>> expr = sqrt(2)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    1.41421
    """
    return expression()

def strain(input: expressionlike) -> expression:
    """
    This defines the (**linear**) engineering strains in Voigt form $(\\epsilon_{xx},\\epsilon_{yy},\\epsilon_{zz},\\gamma_{yz},
    \\gamma_{xz},\\gamma_{xy})$. The input can either be the displacement field or its gradient.

    Note that the shear strain terms in the Voigt form are twice the values in tensorial form:
    $$
        \\gamma_{ij} = 2 \\epsilon_{ij}
    $$

    The tensorial linear strain is defined as
    $$
    \\boldsymbol{\\epsilon} = \\frac{1}{2} \\Bigl[\\nabla \\boldsymbol{u} + \\bigl(\\nabla \\boldsymbol{u}\\bigr)^T  \\Bigr]
    $$

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> u = field("h1xyz")
    >>> engstrain = strain(u)
    >>> engstrain.print()

    See Also
    --------
    greenlagrangestrain
    """
    return expression()

@overload
def sum(data: Sequence[int]) -> None:
    """
    <<INTERNAL>>

    <<INTERNAL>>
    """

@overload
def sum(data: Sequence[float]) -> None: ...
def sum(*args, **kwargs) -> Any: ...
@overload
def symmetrycondition(
    bndphysreg: int, u: field, lagmultorder: int = 0
) -> list[integration]:
    """
    This defines a weak formulation of symmetry condition on the boundary region `bndphysreg`. Depending on, if the `u` field 
    passed is a vector or scalar, the appropriate symmetry condition is formulated. For a vector and scalar field, the symmetry 
    condition is respectively,
    $$
    \\boldsymbol{u} \\cdot \\boldsymbol{n} = 0\\\\
    \\nabla{u} \\cdot \\boldsymbol{n} = 0
    $$

    This function uses a scalar Lagrange multiplier to enforce the symmetry boundary condition. The `lagmultorder` argument sets 
    the interpolation order of the Lagrange multiplier. 
    $$ 
    \\int_{\\Gamma} \\left( \\ \\lambda (\\boldsymbol{u}^{\\prime} \\cdot \\boldsymbol{n}) + {\\lambda}^{\\prime} (\\boldsymbol{u} \\cdot \\boldsymbol{n}) \\ \\right) d \\Gamma = 0 \\qquad, \\text{where $\\boldsymbol{u}$ is a vector field}
    $$

    $$ 
    \\int_{\\Gamma} \\left( \\ \\lambda (\\boldsymbol{\\nabla} {u}^{\\prime} \\cdot \\boldsymbol{n}) + {\\lambda}^{\\prime} (\\boldsymbol{\\nabla} {u} \\cdot \\boldsymbol{n}) \\ \\right) d \\Gamma = 0 \\qquad, \\text{where $u$ is a scalar field}
    $$

    where $\\boldsymbol{n}$ is the unit normal vector. In fluid dynamics, the symmetry condition is equivalent to the slip-condition which states 
    that there is no outflow through the boundary. This is equivalent to velocity vector normal to the boundary being zero. Here, the `u` field 
    passed as the argument is the velocity vector. 

    Examples
    --------
    **Example 1**: `symmetrycondition_doc(bndphysreg:int, u:field, lagmultorder:int=0)`
    >>> mymesh = mesh("quarterdisk.msh")    
    >>> vol = 1; sur = 2; top = 3; sym=4
    >>>
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 2)
    >>> 
    >>> u.setconstraint(sur)  
    >>> 
    >>> E=parameter(); nu=parameter()
    >>> E.setvalue(vol,150e9); nu.setvalue(vol,0.3)
    >>>  
    >>> elasticity = qs.formulation()
    >>>
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), E, nu))
    >>> elasticity += integral(vol, array3x1(0,0,-10)*tf(u))
    >>>
    >>> # symmetry boundary condition
    >>> elasticity += symmetrycondition(sym, u)
    >>> 
    >>> elasticity.solve()

    Note that the symmetry condition also works on fields with harmonics.
    >>> ...
    >>> u = field("h1xyz", [2,3])
    >>> u.setorder(vol, 1)
    >>> ...
    >>> elasticity += symmetrycondition(sym, u)

    The `lagrangemultorder` also determines the type of shape function used by the Lagrange multiplier. If the order is set to zero, 
    shape function of type "one1" (in 2D) or "one2" (in 3D) is used. For order greater than 0, shape function of type "h1" is used.
    >>> ...
    >>> u = field("h1xyz")
    >>>
    >>> elasticity += symmetrycondition(sym, u)     # uses "one2" shape function for Lagrange multiplier.
    >>> elasticity += symmetrycondition(sym, u, 1)  # uses "h1" shape function with interpolation order 1 for Lagrange multiplier.
    >>> elasticity += symmetrycondition(sym, u, 2)  # uses "h1" shape function with interpolation order 2 for Lagrange multiplier.

    **Example 2**: `symmetrycondition_doc(bndphysreg:int, meshdeform:expression, u:field, lagmultorder:int=0)`

    Here, the symmetry boundary condition of `u` is formulated on the mesh deformed by the field `v`.
    >>> ...
    >>> v = field("h1xyz")
    >>> v.setorder(vol, 1)
    >>> ...
    >>> elasticity += symmetrycondition(sym, v, u, 1)

    See Also
    --------
    periodicitycondition, continuitycondition
    """

@overload
def symmetrycondition(
    bndphysreg: int, meshdeform: expressionlike, u: field, lagmultorder: int = 0
) -> list[integration]: ...
def symmetrycondition(*args, **kwargs) -> Any: ...
def t() -> expression:
    """
    This gives the time variable in the form of an expression. The evaluation gives a value equal to `gettime`.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol = 1
    >>> v = field("h1")
    >>> v.setconstraint(vol, sin(2*t()))

    See Also
    --------
    settime, gettime
    """
    return expression()

def tan(input: expressionlike) -> expression:
    """
    This returns an expression that is the $tan$ of input. The input expression is in `radians`.

    Example
    -------
    >>> expr = tan(getpi()/4)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    1
    >>>
    >>> expr = tan(1)
    >>> expr.print()
    Expression size is 1x1
     @ row 0, col 0 :
    1.55741

    See Also
    --------
    sin, cos, asin, acos, atan
    """
    return expression()

def tangent() -> expression:
    """
    This defines a tangent vector with unit norm.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> top=3
    >>> tangent().write(top, "tangent.vtk", 1)
    """
    return expression()

@overload
def tf(input: expressionlike) -> expression:
    """
    This declares a test function field. The test functions are defined only on the region `physreg` which when not provided is set
    to the element integration region.

    Examples
    --------
    **Example 1**: `tf(input:expression)`
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2
    >>> v = field("h1")
    >>> v.setorder(vol, 1)
    >>> projection = formulation()
    >>> projection += integral(vol, dof(v)*tf(v) - 2*tf(v))

    **Example 2**: `tf(input:expression, physreg:int)`
    >>> ...
    >>> projection += integral(vol, dof(v)*tf(v, vol) - 2*tf(v))

    See Also
    --------
    dof
    """

@overload
def tf(input: expressionlike, physreg: int) -> expression: ...
def tf(*args, **kwargs) -> Any: ...
def to2d(input3d: expressionlike) -> expression:
    return expression()

def toggle(switchnumber: int) -> expression:
    return expression()

def trace(a: expressionlike) -> expression:
    """
    This computes the trace of a square matrix expression `a`. The returned expression is a scalar.
    $$
    trace(\\boldsymbol{A}) = \\sum_{i=1}^{n} A_{ii}
    $$

    Example
    -------
    >>> a = array2x2(1,2, 3,4)
    >>> tracea = trace(a)
    >>> tracea.print()
    Expression size is 1x1
     @ row 0, col 0 :
    5
    """
    return expression()

def trackpetscinfo(name: str) -> None: ...
def transpose(input: expressionlike) -> expression:
    """
    This returns an expression that is the transpose of a vector or matrix expression.

    Example
    -------
    >>> colvec = array3x1(1,2,3)
    >>> rowvec = transpose(colvec)
    >>> rowvec.print()
    Expression size is 1x3
     @ row 0, col 0 :
    1
     @ row 0, col 1 :
    2
     @ row 0, col 2 :
    3
    >>> matexpr = expression(3,3, [1,2,3, 4,5,6, 7,8,9])
    >>> transposed = transpose(matexpr)
    """
    return expression()

def vonmises(stress: expressionlike) -> expression:
    """
    This returns the von Mises stress expression corresponding to the 3D stress tensor provided as argument. The stress tensor
    should be provided in Voigt form $(\\sigma_{xx},\\sigma_{yy},\\sigma_{zz},\\sigma_{yz},\\sigma_{xz},\\sigma_{xy})$.

    For 2D plane stress problems all $z$ related components of the stress tensor are $0$. For plane strain problems do not forget
    the term $\\sigma_{zz} = \\nu \\cdot (\\sigma_{xx} + \\sigma_{yy})$.

    Example
    -------
    >>> mymesh = mesh("disk.msh")
    >>> vol=1; sur=2; top=3
    >>> u = field("h1xyz")
    >>> u.setorder(vol, 1)
    >>> u.setconstraint(sur)
    >>>
    >>> # Material properties
    >>> E = 150e9
    >>> nu = 0.3
    >>>
    >>> # Elasticity matrix for isotropic materials
    >>> H = expression(6,6, [1-nu,nu,nu,0,0,0, nu,1-nu,nu,0,0,0, nu,nu,1-nu,0,0,0, 0,0,0,0.5*(1-2*nu),0,0, 0,0,0,0,0.5*(1-2*nu),0, 0,0,0,0,0,0.5*(1-2*nu)])
    >>> H = H * E/((1+nu)*(1-2*nu))
    >>>
    >>> elasticity = formulation()
    >>> elasticity += integral(vol, predefinedelasticity(dof(u), tf(u), H))
    >>>
    >>> # Atmospheric pressure load (volumetric force) on top face deformed by field u (might require a nonlinear iteration)
    >>> elasticity += integral(top, u, -normal(vol)*1e5 * tf(u))
    >>>
    >>> elasticity.solve()
    >>>
    >>> cauchystress = H * strain(u)
    >>> vonmisesstress = vonmises(cauchystress)
    >>>
    >>> vonmisesstress.write(vol, "vonmises.vtk", 1)
    >>> maxvonmises = vonmisesstress.max(vol, 5)[0]
    >>> maxvonmises

    See Also
    --------
    principalstresses
    """
    return expression()

def wallfunction(
    fluidphysreg: int,
    flds: Sequence[field],
    exprs: Sequence[expressionlike],
    wftype: str,
) -> list[expression]: ...
def wavelet(targetfreq: expressionlike, delay: expressionlike) -> expression:
    """
    This creates a Ricker wavelet function with the given target frequency ($f$) provided by the `targetfreq` argument. The wavelet
    can be shifted to the right by setting the `delay` argument to a positive real value.

    $$
        w(t) = (1 - 2 \\pi^2 f^2 (t-\\delta)^2) e^{-\\pi^2 f^2 (t-\\delta)^2} \\newline
    $$
    $$
    \\delta = delay \\times \\frac{1}{f}
    $$

    Note that the `delay` is not directly in time but rather it represents the amount of time period $(T=1/f)$ by which the
    wavelet is delayed. The time period corresponds to that of the target frequency `targetfreq`.
    For example:
    - `delay = 0`,   wavelet's peak amplitude occurs at $t=0$
    - `delay = 1`,   wavelet's peak amplitude occurs at time $t=1 \\times T = 1.0 \\times (1/f)$
    - `delay = 2.5`, wavelet's peak amplitude occurs at time $t=n \\times T = 2.5 \\times (1/f)$

    In the above examples, it is assumed that the startime in a transient simulation is set to zero.

    ![wavelet](./imagesAPI/wavelets.svg)

    # Example
    ---------
    >>> # wavelet with a target frequency of 2MHz and delay of 2.5 time periods
    >>> Vac = wavelet(2e6, 2.5)
    >>>
    >>> ...
    >>>
    >>> # Lump V/Q interaction
    >>> form += lump.V - (Vbias + Vac)
    """
    return expression()

def write(filename: str, io: iodata) -> None: ...
def writecirculationports(filename: str, ports: Sequence[port]) -> None: ...
def writecsvfile(filename: str, header: str, values: Sequence[str]) -> None: ...
def writeshapefunctions(
    filename: str,
    sftypename: str,
    elementtypenumber: int,
    maxorder: int,
    allorientations: bool = False,
) -> None:
    """
    This writes to file all shape functions up to a requested order. It is a convenient tool to visualize the shape functions.

    Example
    -------
    >>> writeshapefunctions("sf.pos", "hcurl", 2, 2)
    """
    ...

def writevector(
    filename: str,
    towrite: Sequence[float],
    delimiter: str = ",",
    writesize: bool = False,
) -> None:
    """
    This writes all the entries of a list given in `towrite` to the file `filename` with the requested `delimiter`.
    The size of the list can also be written at the beginning of a file if `writesize` is set to True.

    Example
    -------
    >>> v = [2.4,3.14,-0.1]
    >>> writevector("vecvals.txt", v)
    2.4,3.14,-0.1
    >>>
    >>> writevector("vecvals.txt", v, ' ')
    2.4 3.14 -0.1
    >>>
    >>> writevector("vecvals.txt", v, '\\n', True)
    3
    2.4
    3.14
    -0.1

    See Also
    --------
    loadvector, printvector
    """
    ...

def zdof(zreals: Sequence[float], zimags: Sequence[float], v: field) -> expression:
    return expression()

def zienkiewiczzhu(input: expressionlike) -> expression:
    """
    This defines a Zienkiewicz-Zhu type error indicator for the argument expression. The value of the returned expression is
    constant over each element. It equals the maximum of the argument expression value jump between that element and any neighbour.
    In the below example, the *zienkiewiczzhu(grad(v))* expression quantifies the discontinuity of the field derivative. For a
    non-scalar arguments the function is applied to each entry and the norm is returned.

    Example
    -------
    >>> sur = 1
    >>> q = shape("quadrangle", sur, [0,0,0, 5,0,0, 5,1,0, 0,1,0], [10,3,10,3])
    >>> mymesh = mesh([q])
    >>>
    >>> v=field("h1"); x=field("x"); y=field("y")
    >>> v.setorder(sur, 1)
    >>>
    >>> criterion = zienkiewiczzhu(grad(v))
    >>> # Target max criterion is 0.05
    >>> maxcrit = ifpositive(criterion-0.05, 1, 0)
    >>> mymesh.setadaptivity(maxcrit, 0, 3)
    >>>
    >>> for i in range(10):
    ...     fct = sin(3*x)/(x*x+1)*sin(getpi()*y)
    ...     v.setvalue(sur, fct)
    ...     v.write(sur, f"v{100+i}.vtk", 1)
    ...     fieldorder(v).write(sur, f"fieldorder{100+i}.vtk", 1)
    ...     criterion.write(sur, f"zienkiewiczzhu{100+i}.vtk", 1)
    ...     relL2err = sqrt(pow(v-fct,2)).integrate(sur,5) / pow(fct,2).integrate(sur,5)
    ...     adapt(2)
    """
    return expression()

def setoutputvalue(
    name: str,
    value: Union[float, Sequence[float]],
    step: Union[float, int, None] = None,
    specifier: Union[str, None] = None,
) -> None:
    """
    Add a value output. Only the main rank (0) will actually write the value.

    **Example**

    >>> qs.setoutputvalue("my scalar", 42.0)
    >>> qs.setoutputvalue("my vector", [1.0, 2.0, 3.0, 4.0])

    **Example transient**

    >>> while qs.gettime() < 1.0 - 1e-08 * 0.1:
    >>>     timestepper.allnext(relrestol=1e-06, maxnumit=1000, timestep=0.1, maxnumnlit=-1)
    >>>
    >>>     qs.setoutputvalue("my vector", [1.0, 2.0, 3.0, 4.0], qs.gettime())
    """
    ...

def setoutputmesh(
    name: str,
    regions: Sequence[int],
    option: int,
    mesh: mesh,
    step: Union[float, int, None] = None,
) -> None:
    """
    Add mesh output that will be available for users.

    Arguments
    ---------

    name: Name for the mesh, used in the filename
    regions: Physical regions that should be included in the mesh files
    option: The option parameter given to mesh.write(...) simcore function
    mesh: Simcore mesh object
    step: Current timestamp or the eigenvalue index. If not applicable, leave unset.
    """
    ...

def setoutputfield(
    fieldname: str,
    region: int,
    expression: expressionlike,
    lagrangeorder: int,
    step: Union[float, int, None] = None,
    specifier: Union[str, None] = None,
    meshdeform: Union[expressionlike, None] = None,
):
    """
    Add a field to output for visualization. The function must be called by all
    ranks, so that all ranks write their own output files.

    **Example**

    >>> qs.setoutputfield("u", qs.selectall(), fld.u, 2)

    **Example transient**

    >>> while qs.gettime() < 1.0 - 1e-08 * 0.1:
    >>>     timestepper.allnext(relrestol=1e-06, maxnumit=1000, timestep=0.1, maxnumnlit=-1)
    >>>
    >>>     qs.setoutputfield("u", reg.all, fld.u, 2, qs.gettime())

    **Example deformed mesh**

    >>> while qs.gettime() < 1.0 - 1e-08 * 0.1:
    >>>     timestepper.allnext(relrestol=1e-06, maxnumit=1000, timestep=0.1, maxnumnlit=-1)
    >>>
    >>>     qs.setoutputfield("u", reg.all, fld.u, 2, qs.gettime(), None, fld.umesh)

    """
    ...

def setoutputfieldiodata(
    fieldname: str,
    data: iodata,
    step: Union[float, int, None] = None,
    specifier: Union[str, None] = None,
):
    """
    Add a field to output for visualization using precalculated iodata object.
    The function must be called by all ranks, so that all ranks write their
    own output files.

    **Example radiation pattern**

    >>> patterndata = qs.computeradiationpattern(mesh.em_radiation_pattern_skin, mesh.em_radiation_pattern, fld.E, qs.getmu0(), qs.getepsilon0(), 20)
    >>> qs.setoutputfieldiodata("Radiation pattern", patterndata)
    """
    ...

def setoutputfieldstate(
    fieldname: str,
    region: int,
    field: field,
    step: Union[float, int, None] = None,
    specifier: Union[str, None] = None,
    sourceports: Sequence[port] = [],
):
    """
    Add raw field state to output. The function must be called by all ranks.

    Outputs written using this function can be used as inputs of other simulations using the
    field initializations feature.

    **Example**

    >>> qs.setoutputfieldstate("u", qs.selectall(), fld.u)
    """
    ...

def setoutputtransientstate(statename: str, timestepper: impliciteuler):
    """
    Add the current state of the transient timestepper to output.

    Outputs written using this function can be used as inputs of other simulations using the
    field initializations feature.

    **Example**

    >>> qs.setoutputtransientstate("state", timestepper)
    >>> qs.loadtransientstate("state", timestepper)
    """
    ...

def setoutputhphistate(
    statename: str,
    H: field,
    phi: field,
    cps: Union[Sequence[port], None] = None,
    statictotransient: Union[bool, None] = None,
    conductingregion: Union[int, None] = None,
    nonconductingregion: Union[int, None] = None,
):
    """
    Add the current state of a H-phi simulation to output.

    Outputs written using this function can be used as inputs of other simulations using the
    H-phi initialization feature.

    **Example**

    >>> # Without transient projection
    >>> qs.setoutputhphistate("state", fld.H, fld.phi, var.cps)
    >>> # In another simulation
    >>> qs.loadhphistate("state", "H", fld.H)
    >>> qs.loadhphistate("state", "phi", fld.phi)
    >>> qs.loadhphistate("state", "ports", var.cps, var.ces)
    >>>
    >>> # Without transient projection and ports
    >>> qs.setoutputhphistate("state", fld.H, fld.phi)
    >>> # In another simulation
    >>> qs.loadhphistate("state", "H", fld.H)
    >>> qs.loadhphistate("state", "phi", fld.phi)
    >>>
    >>> # With transient projection and ports
    >>> qs.setoutputhphistate("state", fld.H, fld.phi, var.cps, True, reg.conducting, reg.nonconducting)
    >>> # In another simulation
    >>> qs.loadhphistate("state", "H", fld.H)
    >>> qs.loadhphistate("state", "phi", fld.phi)
    >>> qs.loadhphistate("state", "ports", var.cps, var.ces)
    """
    ...

def startoutputfileupload(filepaths: Sequence[str]):
    """
    NOTE: Only use this if you need to access custom files written during simulation that might
    timeout or be aborted.

    Start uploading output files. It is not necessary to call this for outputs that have their own
    function such as `setoutputfield`, `setoutputmesh` and `setoutputfieldstate`.
    """
    ...

def loadfieldstate(
    fieldname: str,
    region: int,
    field: field,
    harmonic: Union[int, None] = None,
    step: Union[float, int, None] = None,
    specifier: Union[str, None] = None,
    sourceports: Sequence[port] = [],
    sourceexprs: Sequence[expressionlike] = [],
):
    """
    Load a field state from a file stored using `setoutputfieldstate` in another
    simulation. The optional `harmonic` argument can be used to load the state
    into a specific harmonic of the field.

    **Example**

    >>> qs.setoutputfieldstate("some name", reg.all, field)
    >>> qs.loadfieldstate("some name", reg.all, field)
    """
    ...

def getfieldstatesteps(
    *states: Union[str, tuple[str, str]]
) -> list[Union[int, float, None]]:
    """
    Returns a list of all steps for which all provided field states are available.
    The provided states can be names or (name, specifier) tuples.
    """
    ...

def loadhphistate(
    statename: str,
    targettype: Union[Literal["H"], Literal["phi"], Literal["ports"]],
    target: Union[field, Sequence[port]],
    ces: Union[Sequence[expressionlike], None] = None,
):
    """
    Load H-phi state from a file stored using `setoutputhphistate` in another
    simulation.

    **Example**

    >>> # Without transient projection
    >>> qs.setoutputhphistate("state", fld.H, fld.phi, var.cps)
    >>> # In another simulation
    >>> qs.loadhphistate("state", "H", fld.H)
    >>> qs.loadhphistate("state", "phi", fld.phi)
    >>> qs.loadhphistate("state", "ports", var.cps, var.ces)
    >>>
    >>> # Without transient projection and ports
    >>> qs.setoutputhphistate("state", fld.H, fld.phi)
    >>> # In another simulation
    >>> qs.loadhphistate("state", "H", fld.H)
    >>> qs.loadhphistate("state", "phi", fld.phi)
    >>>
    >>> # With transient projection and ports
    >>> qs.setoutputhphistate("state", fld.H, fld.phi, var.cps, True, reg.conducting, reg.nonconducting)
    >>> # In another simulation
    >>> qs.loadhphistate("state", "H", fld.H)
    >>> qs.loadhphistate("state", "phi", fld.phi)
    >>> qs.loadhphistate("state", "ports", var.cps, var.ces)
    """
    ...

def loadtransientstate(statename: str, timestepper: impliciteuler):
    """
    Load transient state from a file stored using `setoutputtransientstate` in
    another simulation.

    **Example**

    >>> qs.setoutputtransientstate("state", timestepper)
    >>> qs.loadtransientstate("state", timestepper)
    """
    ...

_T = TypeVar("_T")

class cachedproperty(Generic[_T]):
    """
    A decorator for creating a cached property. The target method
    is called only once and the result is cached. The cached value
    can be overridden by assigning a value to the property.
    """

    _getter: Callable[[Any], _T]
    _value: _T | None

    def __init__(self, getter: Callable[[Any], _T]): ...
    def __get__(self, instance: Any, _: type | None = None) -> _T:
        return cast(_T, None)

    def __set__(self, _: Any, value: _T) -> None: ...

expressionlike: TypeAlias = Union[expression, field, parameter, port, float, int]
"expressionlike is a type that accepts anything that can be automatically converted to an `expression`. This type is the union of `expression`, `field`, `parameter`, `port`, `float`, and `int`."
