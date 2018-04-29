import os
import jcamp
import numpy as np
import h5py

functional_groups = ['unfunctionalized alkane', 'alkene', 'alkyne',
                     'alcohol', 'ether', 'amine',
                     'aldehyde', 'ketone', 'carboxylic acid', 'ester', 'amide']
                    # will only consider these 11 groups

def characterize(fp):
    """Returns functionality of molecule."""
    with open(fp, 'r') as f:
        lines = f.readlines()
        if 'M' == lines[-2].strip()[0]:
            return [] # charged species or isotopic :(
        #print(lines[0].strip())
        num_atoms = int(lines[3].strip().split()[0])
        i = 4
        elements = []
        element_dict = {} # element : list of atom ids
        bonds = {}  # atom_id : list of (connected_atom_id, order)
        heteroatoms = False
        functionality = []
        for n in range(num_atoms): # geometry
            element = lines[i].strip().split()[3]
            if element != 'C' and element != 'H':
                heteroatoms = True
            elements.append(element)
            if element_dict.get(element, []) == []:
                element_dict[element] = []
            element_dict[element].append(n)
            bonds[n] = []
            i += 1

        for bond in lines[i:-1]: # connectivity
            bond_data = bond.strip().split()[:3]
            a1, a2, order = bond_data
            bonds[int(a1) - 1].append((int(a2) - 1, int(order)))
            bonds[int(a2) - 1].append((int(a1) - 1, int(order)))
            i += 1

        for o in element_dict.get('O', []): # look for alcohols, ethers, carbonyls
            ether = True
            for bond in bonds[o]:
                if bond[1] == 2 and elements[bond[0]] == 'C': # carbonyl
                    ether = False
                    c = bond[0]
                    ketone = True
                    for bond in bonds[c]:
                        if elements[bond[0]] != 'C' and bond[0] != o: # not a ketone
                            ketone = False
                        if elements[bond[0]] == 'H': # aldehyde
                            functionality.append(6)
                            break
                        elif elements[bond[0]] == 'O' and bond[0] != o: # O-C=O
                            o_2 = bond[0]
                            for bond in bonds[o_2]:
                                if elements[bond[0]] == 'H': # carboxylic acid
                                    functionality.append(8)
                                    break
                                elif elements[bond[0]] == 'C' and bond[0] != c: # ester
                                    functionality.append(9)
                                    break
                            else: # o_2 not bonded to anything
                                functionality.append(9) # carboxylate == ester
                                continue
                            break
                        elif elements[bond[0]] == 'N': # amide
                            functionality.append(10)
                            break
                    else:
                        if ketone: # ketone
                            functionality.append(7)
                        continue
                    break
                elif bond[1] == 1: # look for alcohol and ether
                    if elements[bond[1]] != 'C':
                        ether = False
                    if elements[bond[1]] == 'H': # alcohol
                        functionality.append(3)
                        break
            else:
                if ether: # ether
                    functionality.append(4)
            pass

        amine = False
        for n in element_dict.get('N', []):  # look for amines, make sure not amide
            amine = True
            for bond in bonds[n]:
                if elements[bond[0]] != 'C' and elements[bond[0]] != 'H':
                    amine = False
        else:
            if amine: # amine
                functionality.append(5)

        for c in element_dict.get('C', []): # look for alkenes/alkynes
            for bond in bonds[c]:
                if elements[bond[0]] == 'C': # C-?-C
                    if bond[1] == 2: # alkene
                        functionality.append(1)
                        break
                    elif bond[1] == 3: # alkyne
                        functionality.append(2)
                        break

        if not heteroatoms and len(functionality) == 0:
            return [0]
        elif len(functionality) == 0:
            return [] # throw molecule out, since it contains only exotic functionality

        return list(set(functionality))


def characterize_all_molecules():
    put_to_file = ''

    for fp in filter(lambda f: f.split('.')[1] == 'mol', sorted(os.listdir('nist/mol'))):
        functionality = characterize('nist/mol/' + fp)
        if functionality != []:
            put_to_file += fp.split('.')[0] + ' '
            put_to_file += ' '.join(map(str, sorted(functionality))) + '\n'
            # print(list(map(lambda i: functional_groups[i], functionality)))
        else:
            # os.remove('nist/mol/' + fp)
            # print('Skipped', fp)
            pass

    with open('data/labels.txt', 'w') as f:
            f.write(put_to_file)


def parse_spectrum(nist_id):
    spec = jcamp.JCAMP_reader('nist/jdx/' + nist_id + '-IR.jdx')
    if spec.get('xunits', '1') == '1':
        os.remove('nist/mol/' + nist_id + '.mol')
        print(nist_id + ' has no spectra available.')
        return None, None

    xunits = spec['xunits'].lower()
    yunits = spec['yunits'].lower()
    x = spec['x']
    y = spec['y']

    # convert x to wavenumbers
    if (xunits in ('1/cm', 'cm-1', 'cm^-1')): # already wavenumbers
        pass
    elif (xunits in ('micrometers', 'um', 'wavelength (um)')):
        x = 10000.0 / x
    elif (xunits in ('nanometers', 'nm', 'wavelength (nm)')):
        x = x * 1000.0
        x = 10000.0 / x

    # convert y to absorbance
    if (yunits == 'transmittance'):
        y[y > 1.0] = 1.0

        okay = (y > 0.0)
        y[okay] = np.log10(1.0 / y[okay])
        y[np.logical_not(okay)] = np.nan

    # remove all values over 4000 wn and below 500 wn
    threshold = (x < 4000) & (x > 500)
    x = x[threshold]
    y = y[threshold]

    return x, y

def parse_all_spectra():
    with open('data/labels.txt', 'r') as f:
        for line in f.readlines():
            nist_id = line.split()[0]
            x, y = parse_spectrum(nist_id)
            if x is None:
                continue
            h5f = h5py.File('data/spectra/' + nist_id + '.h5', 'w')
            h5f.create_dataset('x', data=x)
            h5f.create_dataset('y', data=y)
            h5f.close()

characterize_all_molecules()
parse_all_spectra()