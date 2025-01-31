#############################################################################
# Copyright 2016-2017, Anh Tuan Tran, Tal Hassner, Iacopo Masi, and Gerard Medioni
# The SOFTWARE provided in this page is provided "as is", without any guarantee
# made as to its suitability or fitness for any particular use. It may contain
# bugs, so use of this tool is at your own risk. We take no responsibility for
# any damage of any sort that may unintentionally be caused through its use.
# Please, cite the paper:
# @article{tran16_3dmm_cnn,
#   title={Regressing Robust and Discriminative {3D} Morphable Models with a very Deep Neural Network},
#   author={Anh Tran
#       and Tal Hassner
#       and Iacopo Masi
#       and G\'{e}rard Medioni}
#   journal={arXiv preprint},
#   year={2016}
# }
# if you find our code useful.
##############################################################################
import numpy as np
import cv2

rescaleCASIA = [1.9255, 2.2591, 1.9423, 1.6087]
rescaleBB = [1.785974, 1.951171, 1.835600, 1.670403]


def get_mean_shape(model):

    S = model.shapeMU
    numVert = int(S.shape[0] / 3)
    # Final Saving for visualization
    S = np.reshape(S, (numVert, 3))
    return S


def projectBackBFM(model, features):
    alpha = model.shapeEV * 0
    for it in range(0, 99):
        alpha[it] = model.shapeEV[it] * features[it]
    S = np.matmul(model.shapePC, alpha)
    # Adding back average shape
    S = model.shapeMU + S
    numVert = int(S.shape[0] / 3)
    # (Texture)
    beta = model.texEV * 0
    for it in range(0, 99):
        beta[it] = model.texEV[it] * features[it + 99]
    T = np.matmul(model.texPC, beta)
    # Adding back average texture
    T = model.texMU + T
    # Some filtering
    T = [truncateUint8(value) for value in T]
    # Final Saving for visualization
    S = np.reshape(S, (numVert, 3))
    T = np.reshape(T, (numVert, 3))
    return S, T


def projectBackBFM_withExpr(model, features, expr_paras):
    alpha = model.shapeEV * 0
    for it in range(0, 99):
        alpha[it] = model.shapeEV[it] * features[it]
    S = np.matmul(model.shapePC, alpha)

    expr = model.expEV * 0
    for it in range(0, 29):
        expr[it] = model.expEV[it] * expr_paras[it]
    E = np.matmul(model.expPC, expr)

    # Adding back average shape
    S = model.shapeMU + S + model.expMU + E
    numVert = int(S.shape[0] / 3)

    # (Texture)
    beta = model.texEV * 0
    for it in range(0, 99):
        beta[it] = model.texEV[it] * features[it + 99]
    T = np.matmul(model.texPC, beta)
    # Adding back average texture
    T = model.texMU + T
    # Some filtering
    T = [truncateUint8(value) for value in T]
    # Final Saving for visualization
    S = np.reshape(S, (numVert, 3))
    T = np.reshape(T, (numVert, 3))
    return S, T


def projectBackBFM_withEP(model, features, expr_paras, pose_paras):
    alpha = model.shapeEV * 0
    for it in range(0, 99):
        alpha[it] = model.shapeEV[it] * features[it]
    S = np.matmul(model.shapePC, alpha)

    # Expression
    expr = model.expEV * 0
    for it in range(0, 29):
        expr[it] = model.expEV[it] * expr_paras[it]
    E = np.matmul(model.expPC, expr)

    # Adding back average shape
    S = model.shapeMU + S + model.expMU + E
    numVert = int(S.shape[0] / 3)

    # Pose
    #PI = np.array([[  2.88000000e+03, 0.00000000e+00, 1.12000000e+02], [0.00000000e+00, 2.88000000e+03, 1.12000000e+02], [0, 0, 1]]);
    r = pose_paras[0:3]
    r[1] = -r[1]
    r[2] = -r[2]
    t = pose_paras[3:6]
    t[0] = -t[0]
    # print r.shape, t.shape
    R, jacobian = cv2.Rodrigues(r, None)
    # print R

    S = np.reshape(S, (numVert, 3))
    # print S.shape
    S_RT = np.matmul(R, np.transpose(S)) + np.reshape(t, [3, 1])
    #S_RT = np.matmul(PI, S_RT)
    S_RT = np.transpose(S_RT)

    # (Texture)
    beta = model.texEV * 0
    for it in range(0, 99):
        beta[it] = model.texEV[it] * features[it + 99]
    T = np.matmul(model.texPC, beta)
    # Adding back average texture
    T = model.texMU + T
    # Some filtering
    T = [truncateUint8(value) for value in T]
    # Final Saving for visualization
    S = np.reshape(S_RT, (numVert, 3))
    T = np.reshape(T, (numVert, 3))

    return S, T


def truncateUint8(val):
    if val < 0:
        return 0
    elif val > 255:
        return 255
    else:
        return val


def write_ply(fname, S, T, faces):
    nV = S.shape[0]
    nF = faces.shape[0]
    f = open(fname, 'w')
    f.write('ply\n')
    f.write('format ascii 1.0\n')
    f.write('element vertex ' + str(nV) + '\n')
    f.write('property float x\n')
    f.write('property float y\n')
    f.write('property float z\n')
    f.write('property uchar red\n')
    f.write('property uchar green\n')
    f.write('property uchar blue\n')
    f.write('element face ' + str(nF) + '\n')
    f.write('property list uchar int vertex_indices\n')
    f.write('end_header\n')
    for i in range(0, nV):
        f.write('%0.4f %0.4f %0.4f %d %d %d\n' % (S[i, 0], S[i, 1], S[i, 2], T[i, 0], T[i, 1], T[i, 2]))

    for i in range(0, nF):
        f.write('3 %d %d %d\n' % (faces[i, 0], faces[i, 1], faces[i, 2]))
    f.close()


def write_ply_textureless(fname, S, faces):
    nV = S.shape[0]
    nF = faces.shape[0]
    f = open(fname, 'w')
    f.write('ply\n')
    f.write('format ascii 1.0\n')
    f.write('element vertex ' + str(nV) + '\n')
    f.write('property float x\n')
    f.write('property float y\n')
    f.write('property float z\n')
    f.write('element face ' + str(nF) + '\n')
    f.write('property list uchar int vertex_indices\n')
    f.write('end_header\n')

    for i in range(0, nV):
        f.write('%0.4f %0.4f %0.4f\n' % (S[i, 0], S[i, 1], S[i, 2]))

    for i in range(0, nF):
        f.write('3 %d %d %d\n' % (faces[i, 0], faces[i, 1], faces[i, 2]))

    f.close()


def cropImg(img, tlx, tly, brx, bry, img2, rescale):
    l = float(tlx)
    t = float(tly)
    ww = float(brx - l)
    hh = float(bry - t)
    # Approximate LM tight BB
    h = img.shape[0]
    w = img.shape[1]
    cv2.rectangle(img2, (int(l), int(t)), (int(brx), int(bry)), (0, 255, 255), 2)
    cx = l + int(ww / 2)
    cy = t + int(hh / 2)
    tsize = int(max(ww, hh) / 2)
    l = cx - tsize
    t = cy - tsize

    # Approximate expanded bounding box
    bl = int(round(cx - rescale[0] * tsize))
    bt = int(round(cy - rescale[1] * tsize))
    br = int(round(cx + rescale[2] * tsize))
    bb = int(round(cy + rescale[3] * tsize))
    nw = int(br - bl)
    nh = int(bb - bt)
    imcrop = np.zeros((nh, nw, 3), dtype="uint8")

    ll = 0
    if bl < 0:
        ll = -bl
        bl = 0
    rr = nw
    if br > w:
        rr = w + nw - br
        br = w
    tt = 0
    if bt < 0:
        tt = -bt
        bt = 0
    bbb = nh
    if bb > h:
        bbb = h + nh - bb
        bb = h
    imcrop[tt:bbb, ll:rr, :] = img[bt:bb, bl:br, :]
    return imcrop


def cropByInputLM(img, lms, img2):
    nLM = lms.shape[0]
    lms_x = [lms[i, 0] for i in range(0, nLM)]
    lms_y = [lms[i, 1] for i in range(0, nLM)]
    return cropImg(img, min(lms_x), min(lms_y), max(lms_x), max(lms_y), img2, rescaleCASIA)


def cropByFaceDet(img, detected_face, img2):
    return cropImg(img, detected_face.left(), detected_face.top(),
                   detected_face.right(), detected_face.bottom(), img2, rescaleBB)


def cropByLM(img, shape, img2):
    nLM = shape.num_parts
    lms_x = [shape.part(i).x for i in range(0, nLM)]
    lms_y = [shape.part(i).y for i in range(0, nLM)]
    return cropImg(img, min(lms_x), min(lms_y), max(lms_x), max(lms_y), img2, rescaleCASIA)
